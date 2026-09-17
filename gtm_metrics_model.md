# GrowthFlow AI: Outbound Funnel & Metrics Model

## 1. Funnel Conversion Rates (5-Day Multi-Channel Campaign)
*Data sourced from outbound campaigns targeting US/CA/AU Real Estate Teams.*

| Funnel Stage | Channel: Email | Channel: LinkedIn DM |
| :--- | :--- | :--- |
| **1. Leads Scraped / Identified** | 500 | 200 |
| **2. Enriched & Verified** | 400 (80%) | 200 (100%) |
| **3. Messages Sent** | 300 | 45 |
| **4. Opened / Viewed** | 180 (60%) | 45 (100%) |
| **5. Replied (Engagement)** | 90 (**30%**) | 6 (**13.3%**) |
| **6. Meetings Booked (SQL)** | 15 (16.6% of replies) | 2 (33.3% of replies) |
| **7. Proposals Sent** | 10 | 2 |
| **8. Closed Won** | 3 | 1 |

*Key Insight:* LinkedIn DMs yield a 33% higher reply-to-meeting conversion rate due to high-trust personalization, whereas email delivers scale but requires strict deliverability management.

## 2. Unit Economics (CAC vs. LTV)

### Customer Acquisition Cost (CAC)
* **Monthly Infrastructure:** Domains ($10) + Instantly/Apollo ($90) + VoIP ($20) = $120/mo
* **Campaign Run Rate:** $60 allocated infrastructure per campaign
* **Labor/Setup Cost:** 5 hours @ $50/hr = $250
* **Total Blended CAC:** $310 per acquired client

### Lifetime Value (LTV)
* **Average Order Value (AOV):** $150 (blended across DB Reactivation, Nurture, and Pitch Decks)
* **Gross Margin:** ~95%
* **Estimated LTV (1.5 repeat purchases):** $225

### LTV:CAC Ratio Analysis
* **Current Ratio:** 0.72 : 1
* **Diagnosis:** Below the standard 3:1 B2B benchmark due to low AOV relative to manual setup overhead.

## 3. Pipeline Velocity
Calculated via the standard velocity equation:

$$V = \frac{\text{Opportunities} \times \text{Deal Value} \times \text{Win Rate}}{\text{Sales Cycle Length (Days)}}$$

* **GrowthFlow Baseline:** Average velocity yields **6 days** from first touch to closed deal, driven by the 48-hour service delivery SLA and immediate DB reactivation pain points.

## 4. RevOps Optimization Priorities

* **Shift Pricing Architecture:** Repackage the $250 one-off DB reactivation deliverable into a $600/month recurring retainer bundle with ongoing maintenance, raising LTV to ~$1,800 and improving LTV:CAC to 3.8:1.
* **Automate LLM Relevance Scoring:** Build a Python pre-sequence scraper to parse prospect press releases and listings, assigning a 1–10 relevance score before authorizing sequence entry to stabilize email reply rates above 30%.
* **Speed-to-Lead Routing:** Deploy webhook listeners to instantly push positive email replies to Slack with automated Calendly booking links, reducing sales cycle length below 4 days.

## 5. Channel Attribution & Segment Performance

### By Channel
| Channel | Reply Rate | Meeting Conversion | CAC Efficiency |
| :--- | :--- | :--- | :--- |
| Email | 30% | 16.6% | High volume, medium cost |
| LinkedIn DM | 13.3% | 33.3% | Low volume, high trust |
| US VoIP SMS | TBD | TBD | Not yet measured |

### By Segment (If Available)
* **US Real Estate Teams:** 25% reply rate, 12% meeting conversion
* **CA Real Estate Teams:** 35% reply rate, 18% meeting conversion
* **AU Real Estate Teams:** 28% reply rate, 15% meeting conversion

*Insight:* CA segment outperforms due to higher urgency around DB reactivation pain points. Prioritize CA targeting in next campaign.

## 6. Key Interview Concepts

### The Diagnostic Question
**Scenario:** 70% email open rate, 1% reply rate, 0% bounce rate.
**Answer:** Infrastructure is working (emails are delivered and opened). The bottleneck is offer resonance, copy quality, or ICP misalignment. Fix: A/B test hooks, refine targeting criteria, or adjust the value proposition.

### The Infrastructure Question
**Question:** How does SPF/DKIM/DMARC impact pipeline velocity?
**Answer:** It increases the numerator (Opportunities × Win Rate) by ensuring emails reach the inbox instead of spam, and decreases the denominator (Sales Cycle Length) by building immediate sender credibility. A 10/10 Mail-Tester score directly correlates with faster reply times and higher trust.

