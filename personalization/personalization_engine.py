"""
Day 46 — AI Personalization Engine with Hallucination Guardrails
Reads Day 43 enrichment data and generates highly contextual, 
non-spammy email first-lines, validated by Pydantic.
"""
import os
import json
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ValidationError
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ─── The Strict Output Schema ──────────────────────────────────
class EmailHook(BaseModel):
    first_line: str = Field(..., description="A casual, highly personalized first line. Max 25 words. NEVER use 'I hope this finds you well' or 'I am reaching out because'.")
    fact_used: str = Field(..., description="The exact fact from the context used to write the line. If no context, say 'None'.")
    
    @field_validator('first_line')
    @classmethod
    def check_length_and_tone(cls, v: str) -> str:
        if len(v.split()) > 25:
            raise ValueError("First line is too long. Must be under 25 words.")
        spam_phrases = ["hope this finds you", "reaching out", "thrilled to", "synergy"]
        if any(phrase in v.lower() for phrase in spam_phrases):
            raise ValueError("Contains spammy sales phrases.")
        return v

# ─── The Generation Logic ──────────────────────────────────────
def generate_hook(domain: str, context: str) -> dict:
    # Guardrail 1: If Day 43 found no news, don't let the LLM hallucinate.
    if "No recent news found" in context or "Search error" in context:
        return {
            "first_line": f"I've been following {domain}'s work in the real estate space and love your platform's approach.",
            "fact_used": "Fallback: No recent news available."
        }

    prompt = f"""
    You are an expert B2B copywriter. Write the opening line of a cold email to a decision-maker at {domain}.
    
    Recent Context/News: {context}
    
    Rules:
    1. Reference a specific, recent event, funding round, or tech adoption from the context.
    2. Sound like a peer, not a salesperson. 
    3. Keep it under 25 words.
    4. DO NOT pitch a product yet. Just build rapport.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EmailHook,
            ),
        )
        # Pydantic validates the JSON automatically!
        validated_data = EmailHook.model_validate_json(response.text)
        return validated_data.model_dump()
        
    except ValidationError as e:
        # Guardrail 2: If the LLM wrote a spammy/long line, catch it and fallback.
        return {
            "first_line": f"Been following {domain}'s recent moves in the market.",
            "fact_used": f"Fallback triggered due to validation error: {str(e)[:50]}"
        }
    except Exception as e:
        return {"first_line": f"Checking out {domain}.", "fact_used": f"Error: {e}"}

# ─── Pipeline Orchestration ────────────────────────────────────
def run_engine():
    csv_path = Path(__file__).parent / "enriched_leads.csv"
    df = pd.read_csv(csv_path)
    
    print(f"\n✍️  Generating personalized hooks for {len(df)} leads...\n")
    
    hooks = []
    for _, row in df.iterrows():
        domain = row['domain']
        context = row['raw_context']
        
        print(f"  -> Writing hook for {domain}...")
        result = generate_hook(domain, context)
        
        hooks.append({
            "domain": domain,
            "icp_score": row['icp_score'],
            "personalized_first_line": result["first_line"],
            "fact_cited": result["fact_used"]
        })

    out_df = pd.DataFrame(hooks)
    out_path = Path(__file__).parent / "personalized_outreach.csv"
    out_df.to_csv(out_path, index=False)
    
    print(f"\n✅ Done! Saved to {out_path.name}")
    print("\n--- Preview of Top 3 Hot Leads ---")
    hot_leads = out_df[out_df['icp_score'] >= 70].head(3)
    for _, r in hot_leads.iterrows():
        print(f"\n[{r['domain']}] (Score: {r['icp_score']})")
        print(f"  Line: \"{r['personalized_first_line']}\"")
        print(f"  Fact: {r['fact_cited']}")

if __name__ == "__main__":
    run_engine()