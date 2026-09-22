# 📬 GrowthFlow AI: Outbound Deliverability Playbook

## The Holy Trinity of Email Auth
Before sending a single cold email, the sending domain MUST pass these three DNS checks.

### 1. SPF (Sender Policy Framework) - "The Passport"
*   **What it is:** A TXT record listing the IP addresses and services (like Instantly, Smartlead, or Google Workspace) authorized to send email on behalf of your domain.
*   **The Rule:** Never exceed 10 DNS lookups in your SPF record, or it will fail validation.
*   **GrowthFlow Setup:** `v=spf1 include:_spf.google.com include:spf.instantly.ai ~all`

### 2. DKIM (DomainKeys Identified Mail) - "The Wax Seal"
*   **What it is:** A cryptographic signature attached to every email. The receiving server uses the public key in your DNS to verify the email wasn't tampered with in transit.
*   **The Rule:** Every ESP (Email Service Provider) you use needs its own unique DKIM selector.

### 3. DMARC (Domain-based Message Authentication) - "The Bouncer Instructions"
*   **What it is:** A policy that tells Gmail/Outlook what to do if SPF or DKIM fails.
*   **The 2024+ Gmail/Yahoo Requirement:** You MUST have a DMARC record. 
*   **The Progression:** 
    *   `p=none` (Monitor only - use this for the first 2 weeks of warmup)
    *   `p=quarantine` (Send failures to spam)
    *   `p=reject` (Hard block failures - use only when fully confident)

## The "Secondary Domain" Strategy
**Never send cold outbound from your primary corporate domain.** 
If `growthflowai.site` gets blacklisted for spam, internal team emails and inbound customer replies will go to spam. 
*   **Correct Setup:** Buy secondary domains (e.g., `getgrowthflow.com`, `growthflow-team.com`).
*   **Forwarding:** Set up a 301 redirect from the secondary domains to the primary website.
*   **MX Records:** Ensure secondary domains have valid MX records (even if they just route to a dummy inbox), or Gmail will flag them as fake.

## The Pre-Flight Checklist (Mail-Tester 10/10)
Before launching a new sequence, send a test email to [mail-tester.com](https://www.mail-tester.com).
- [ ] SPF, DKIM, DMARC all pass (0 points lost)
- [ ] No spammy words in the subject line ("Free", "Guarantee", "!!!")
- [ ] HTML to Text ratio is balanced (don't send image-only emails)
- [ ] Domain is not on any Spamhaus blacklists
- [ ] Includes a valid List-Unsubscribe header (Mandatory for Gmail/Yahoo)