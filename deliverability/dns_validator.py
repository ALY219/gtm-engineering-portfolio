"""
Day 45 — Pre-Send DNS Deliverability Validator
Checks SPF, DMARC, and common DKIM selectors for outbound readiness.
"""
import sys
import dns.resolver

def check_spf(domain: str) -> dict:
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for rdata in answers:
            for txt_string in rdata.strings:
                txt = txt_string.decode('utf-8')
                if txt.startswith("v=spf1"):
                    return {"status": "✅ PASS", "record": txt}
        return {"status": "❌ FAIL", "record": "No SPF record found"}
    except Exception:
        return {"status": "❌ FAIL", "record": "DNS Error / No TXT records"}

def check_dmarc(domain: str) -> dict:
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
        for rdata in answers:
            for txt_string in rdata.strings:
                txt = txt_string.decode('utf-8')
                if txt.startswith("v=DMARC1"):
                    # Extract policy (p=none, p=quarantine, p=reject)
                    policy = "unknown"
                    for part in txt.split(";"):
                        if "p=" in part:
                            policy = part.strip()
                    return {"status": "✅ PASS", "record": txt, "policy": policy}
        return {"status": "❌ FAIL", "record": "No DMARC record found"}
    except Exception:
        return {"status": "❌ FAIL", "record": "No DMARC record configured"}

def check_dkim(domain: str) -> dict:
    # Common DKIM selectors used by Google, Microsoft, and ESPs
    selectors = ["google", "k1", "selector1", "selector2", "default", "mail", "mandrill", "brevo"]
    found = []
    for sel in selectors:
        try:
            answers = dns.resolver.resolve(f"{sel}._domainkey.{domain}", 'TXT')
            for rdata in answers:
                for txt_string in rdata.strings:
                    txt = txt_string.decode('utf-8')
                    if "v=DKIM1" in txt or "k=rsa" in txt:
                        found.append(sel)
        except Exception:
            continue
            
    if found:
        return {"status": "✅ PASS", "selectors": found}
    return {"status": "⚠️  WARN", "selectors": [], "note": "No common selectors found (might be custom)"}

def audit_domain(domain: str):
    print(f"\n{'='*50}")
    print(f"🔍 Auditing Deliverability for: {domain}")
    print(f"{'='*50}")

    spf = check_spf(domain)
    print(f"[SPF]   {spf['status']}")
    if 'record' in spf: print(f"        {spf['record'][:100]}...")

    dmarc = check_dmarc(domain)
    print(f"[DMARC] {dmarc['status']}")
    if 'policy' in dmarc: print(f"        Policy: {dmarc['policy']}")
    if 'record' in dmarc: print(f"        {dmarc['record']}")

    dkim = check_dkim(domain)
    print(f"[DKIM]  {dkim['status']}")
    if dkim['selectors']: print(f"        Found selectors: {', '.join(dkim['selectors'])}")
    if 'note' in dkim: print(f"        {dkim['note']}")
    
    print(f"{'='*50}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py -3.14 dns_validator.py <domain.com>")
        sys.exit(1)
    
    target = sys.argv[1]
    audit_domain(target)