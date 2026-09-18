"""
Day 43 — AI-Native Enrichment Pipeline ("Mini-Clay")

Takes raw domain list → web-searches recent context → LLM-scores ICP fit
→ outputs a scored CSV ready for CRM routing.

Design decisions (interview-ready):
- google-genai (supported) over google.generativeai (EOL)
- ddgs (renamed package) over duckduckgo-search
- Pydantic constraints in descriptions, not ge/le (Gemini Schema proto rejects min/max)
- Exponential backoff on 429s (free tier: 5 RPM)
- Per-lead error isolation — one bad lead never kills the batch
- Token + cost tracking for unit economics visibility
"""

import os
import time
import json
import csv
from datetime import datetime
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.genai import errors
from ddgs import DDGS

# ─── Configuration ──────────────────────────────────────────────────────
load_dotenv()  # walks up to repo root/.env

MODEL = "gemini-2.5-flash"
FREE_TIER_RPM = 5
RETRY_ATTEMPTS = 4
BASE_BACKOFF_S = 15          # Gemini free tier often asks for ~60s wait
SEARCH_SLEEP_S = 2           # politeness between DuckDuckGo queries
SCORE_SLEEP_S = 2            # spread LLM calls across the minute window
HOT_LEAD_THRESHOLD = 70

# Gemini 2.5 Flash pricing (USD per 1M tokens) — free tier is $0,
# but we track paid-equivalent cost for unit-economics visibility.
INPUT_PRICE_PER_M = 0.30
OUTPUT_PRICE_PER_M = 2.50

# ─── Schema ─────────────────────────────────────────────────────────────
# Constraints live in descriptions because the Gemini Schema proto
# rejects minimum/maximum fields (the crash we hit on Day 43).
class LeadScore(BaseModel):
    score: int = Field(
        ...,
        description="ICP fit score, integer from 0 to 100 (inclusive). "
                    "Be strict: only 80+ for clearly strong fits."
    )
    reasoning: str = Field(
        ...,
        description="One concise sentence explaining the score."
    )
    suggested_hook: str = Field(
        ...,
        description="One sentence personalized email hook referencing a specific recent event, funding round, or tech adoption found in the context. Must cite a real fact from the context."
    )

# ─── Clients ────────────────────────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY missing from .env at repo root")

client = genai.Client(api_key=api_key)

# ─── Enrichment: web search ────────────────────────────────────────────
def get_company_context(domain: str) -> str:
    """Scrape 3 recent news/results about the company."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"{domain} real estate technology news OR funding OR growth",
                max_results=3,
            ))
        if not results:
            return "No recent news found."
        return " | ".join(r.get("body", "") for r in results if r.get("body"))
    except Exception as e:
        return f"Search error: {type(e).__name__}: {e}"

# ─── Scoring: LLM with backoff ─────────────────────────────────────────
def score_lead(domain: str, context: str) -> tuple[dict, dict]:
    """
    Returns (score_data, usage_stats).
    Uses exponential backoff on 429s. Raises on non-retryable errors.
    """
    prompt = f"""You are a B2B GTM Engineer qualifying leads for an AI-automation agency
targeting real-estate companies.

Domain: {domain}
Recent context/news: {context}

Score this lead from 0 to 100 based on:
- Size and scale (larger teams need more automation)
- Tech-forwardness (are they adopting tech already?)
- Recent growth/funding (do they have budget?)

Return JSON matching the LeadScore schema. Be strict and fact-based:
do NOT fabricate news that isn't in the context."""

    last_err: Optional[Exception] = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LeadScore,
                ),
            )
            usage = {
                "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
            }
            return json.loads(response.text), usage

        except errors.ClientError as e:
            last_err = e
            if e.code == 429 and attempt < RETRY_ATTEMPTS - 1:
                wait = BASE_BACKOFF_S * (2 ** attempt)
                print(f"    ⏳ 429 rate-limited. Backing off {wait}s "
                      f"(attempt {attempt + 1}/{RETRY_ATTEMPTS})...")
                time.sleep(wait)
                continue
            # 4xx (non-429) are not retryable — fail fast
            raise

        except errors.ServerError as e:
            last_err = e
            if attempt < RETRY_ATTEMPTS - 1:
                wait = BASE_BACKOFF_S * (2 ** attempt)
                print(f"    ⏳ Server error {e.code}. Backing off {wait}s...")
                time.sleep(wait)
                continue
            raise

    raise RuntimeError(f"Exhausted retries: {last_err}")

# ─── Cost math ─────────────────────────────────────────────────────────
def estimate_cost(total_in: int, total_out: int) -> float:
    return (total_in / 1_000_000) * INPUT_PRICE_PER_M + \
           (total_out / 1_000_000) * OUTPUT_PRICE_PER_M

# ─── Pipeline orchestration ────────────────────────────────────────────
def run_pipeline(input_csv: str = "raw_leads.csv",
                 output_csv: str = "enriched_leads.csv") -> None:

    df = pd.read_csv(input_csv)
    print(f"\n🚀 Starting enrichment for {len(df)} leads @ {datetime.now().strftime('%H:%M:%S')}\n")

    enriched: list[dict] = []
    total_in, total_out = 0, 0
    errors_count = 0

    for i, row in df.iterrows():
        domain = str(row["domain"]).strip()
        print(f"[{i + 1}/{len(df)}] {domain}")

        # 1. Enrich
        context = get_company_context(domain)
        time.sleep(SEARCH_SLEEP_S)

        # 2. Score (isolated — one failure won't kill the batch)
        try:
            score_data, usage = score_lead(domain, context)
            total_in += usage["input_tokens"]
            total_out += usage["output_tokens"]
        except Exception as e:
            print(f"    ❌ Scoring failed: {type(e).__name__}: {e}")
            score_data = {
                "score": 0,
                "reasoning": f"Scoring error: {type(e).__name__}",
                "suggested_hook": "",
            }
            usage = {"input_tokens": 0, "output_tokens": 0}
            errors_count += 1

        enriched.append({
            "domain": domain,
            "icp_score": int(score_data["score"]),
            "reasoning": score_data["reasoning"],
            "email_hook": score_data["suggested_hook"],
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "raw_context": context[:300] + ("..." if len(context) > 300 else ""),
            "enriched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })

        time.sleep(SCORE_SLEEP_S)

    # ─── Persist + summarize ───────────────────────────────────────────
    out_df = pd.DataFrame(enriched)
    out_df.to_csv(output_csv, index=False)

    hot = out_df[out_df["icp_score"] >= HOT_LEAD_THRESHOLD]
    warm = out_df[(out_df["icp_score"] >= 40) & (out_df["icp_score"] < HOT_LEAD_THRESHOLD)]
    cold = out_df[out_df["icp_score"] < 40]

    cost = estimate_cost(total_in, total_out)

    print(f"\n{'=' * 60}")
    print(f"✅ Pipeline complete → {output_csv}")
    print(f"{'=' * 60}")
    print(f"Total leads processed : {len(enriched)}")
    print(f"Scoring errors        : {errors_count}")
    print(f"🔥 Hot  (≥{HOT_LEAD_THRESHOLD})        : {len(hot)}")
    print(f"🟡 Warm (40–{HOT_LEAD_THRESHOLD - 1})     : {len(warm)}")
    print(f"🔵 Cold (<40)        : {len(cold)}")
    print(f"Tokens used           : {total_in:,} in / {total_out:,} out")
    print(f"Paid-equivalent cost  : ${cost:.4f}  (free tier: $0.00)")
    print(f"{'=' * 60}\n")

    if len(hot):
        print("Hot leads ready for Day-42 HubSpot router:")
        for _, r in hot.iterrows():
            print(f"  • {r['domain']:30s}  score={r['icp_score']:3d}  → {r['reasoning']}")

if __name__ == "__main__":
    run_pipeline()