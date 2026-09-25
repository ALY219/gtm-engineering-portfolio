"""
Day 48 — SQL Analytics & Outbound ROI Tracking
Interrogates the SQLite state machine to calculate campaign health, 
sequence attrition, and estimated pipeline value.
"""
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "campaign_state.db"

def run_analytics():
    # Connect to the Day 47 State Machine
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*60)
    print("📊 GTM ENGINEERING: OUTBOUND ROI & PIPELINE ANALYTICS")
    print("="*60)
    
    # ─── QUERY 1: Campaign Health & Status Breakdown ───────────
    # What percentage of our database is actively working vs completed?
    q1 = """
        SELECT 
            status, 
            COUNT(domain) as lead_count,
            ROUND(COUNT(domain) * 100.0 / (SELECT COUNT(*) FROM campaign_state), 2) as pct_of_total
        FROM campaign_state
        GROUP BY status;
    """
    print("\n[1] Campaign State Breakdown:")
    print(pd.read_sql_query(q1, conn).to_string(index=False))
    
    # ─── QUERY 2: Sequence Depth & Attrition ───────────────────
    # Where are leads dropping off in the drip campaign?
    q2 = """
        SELECT 
            step, 
            COUNT(domain) as leads_at_step
        FROM campaign_state
        GROUP BY step
        ORDER BY step;
    """
    print("\n[2] Sequence Depth (Drip Attrition):")
    print(pd.read_sql_query(q2, conn).to_string(index=False))
    
    # ─── QUERY 3: The "CFO Query" (Simulated Pipeline ROI) ─────
    # Translating email sends into dollars using standard SaaS funnel math.
    # Assumptions: 5% reply rate, 20% meeting show rate, $15,000 ACV (Annual Contract Value)
    q3 = """
        SELECT 
            COUNT(CASE WHEN last_sent_at IS NOT NULL THEN 1 END) as total_emails_sent,
            COUNT(CASE WHEN step >= 2 THEN 1 END) as leads_reaching_step_2,
            ROUND(COUNT(CASE WHEN last_sent_at IS NOT NULL THEN 1 END) * 0.05, 0) as est_meetings_booked,
            ROUND(COUNT(CASE WHEN last_sent_at IS NOT NULL THEN 1 END) * 0.05 * 0.20 * 15000, 2) as est_pipeline_value_usd
        FROM campaign_state;
    """
    print("\n[3] Estimated Pipeline ROI (Assumes 5% reply, 20% show, $15k ACV):")
    print(pd.read_sql_query(q3, conn).to_string(index=False))
    
    print("\n" + "="*60)
    print("✅ Analytics complete. Data ready for executive reporting.\n")
    
    conn.close()

if __name__ == "__main__":
    run_analytics()