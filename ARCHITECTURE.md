\# HubSpot Integration Architecture



\## Overview

A bidirectional integration between the GrowthFlow AI Enrichment Pipeline and HubSpot CRM.

\- \*\*Inbound:\*\* Pushes AI-scored "Hot Leads" (ICP Score $\\ge$ 70) into HubSpot as Sales Qualified Leads (SQLs).

\- \*\*Outbound:\*\* (Future) Listens for lifecycle stage changes to trigger onboarding workflows.



\## Authentication \& Security

\- \*\*Method:\*\* HubSpot \*\*Service Key\*\* (Private App legacy alternative).

\- \*\*Scoping:\*\* Least-privilege access granted only for `crm.objects.contacts` and `crm.objects.deals` (Read/Write).

\- \*\*Secret Management:\*\* Key stored in local `.env` (git-ignored), never hardcoded.



\## The Routing Engine (Python vs. n8n)

While many GTM workflows use n8n/Zapier, this router is implemented in \*\*Python\*\* (`push\_to\_hubspot.py`) to ensure:

1\.  \*\*Type Safety:\*\* Pydantic models validate lead data before it touches the CRM.

2\.  \*\*Testability:\*\* The routing logic can be unit-tested (unlike visual nodes).

3\.  \*\*Idempotency:\*\* The client checks for existing contacts (by email) to prevent duplicates (handling `409 Conflict` gracefully).



\## Resilience Patterns

\- \*\*Exponential Backoff:\*\* The `hubspot\_client.py` wrapper retries on `429 Too Many Requests` with exponential delays (1s, 2s, 4s).

\- \*\*Error Isolation:\*\* A failure to score or push one lead does not crash the batch; errors are logged and the pipeline continues.



\## Data Flow

1\.  \*\*Enrichment:\*\* `enrichment\_pipeline.py` scrapes news \& scores ICP fit (0-100).

2\.  \*\*Filter:\*\* `push\_to\_hubspot.py` filters for `icp\_score >= 70`.

3\.  \*\*Push:\*\* Valid leads are created in HubSpot with `lifecyclestage = salesqualifiedlead`.

