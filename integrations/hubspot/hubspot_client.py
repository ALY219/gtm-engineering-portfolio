"""HubSpot client for the GrowthFlow lead router.
Auth: service key from .env, sent as Bearer token.
Policy: search-before-write (idempotency), backoff on 429."""
import os, time, requests
from dotenv import load_dotenv
load_dotenv()

KEY = os.getenv("HUBSPOT_SERVICE_KEY")
BASE = "https://api.hubapi.com/crm/v3/objects"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

def with_backoff(fn, *a, tries=4, **kw):
    """On 429: exponential backoff (1s,2s,4s), honor Retry-After if present."""
    for attempt in range(tries):
        r = fn(*a, **kw)
        if r.status_code != 429:
            return r
        time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
    return r

def find_by_email(email):
    """Dedupe check. POST /search (indexed) not GET /contacts (full scan)."""
    r = with_backoff(requests.post, f"{BASE}/contacts/search", headers=H,
        json={"filterGroups": [{"filters": [
            {"propertyName": "email", "operator": "EQ", "value": email}]}],
            "properties": ["email", "lifecyclestage"]})
    r.raise_for_status()
    res = r.json().get("results", [])
    return res[0]["id"] if res else None

def create_contact(props):
    """409-aware: returns ID, or None if duplicate (caller decides to PATCH)."""
    r = with_backoff(requests.post, f"{BASE}/contacts", headers=H, json={"properties": props})
    return None if r.status_code == 409 else (r.raise_for_status() or r.json()["id"])

def update_contact(cid, props):
    r = with_backoff(requests.patch, f"{BASE}/contacts/{cid}", headers=H, json={"properties": props})
    r.raise_for_status()
    return r.json()["id"]

def set_lifecycle(email, stage):
    """stage: lead | marketingqualifiedlead | salesqualifiedlead | opportunity | customer"""
    cid = find_by_email(email)
    if not cid:
        raise ValueError(f"No contact for {email}")
    return update_contact(cid, {"lifecyclestage": stage})

def create_deal(props):
    """SQL branch: open a deal for hot leads."""
    r = with_backoff(requests.post, f"{BASE}/deals", headers=H, json={"properties": props})
    r.raise_for_status()
    return r.json()["id"]