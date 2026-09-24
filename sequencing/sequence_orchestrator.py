"""
Day 47 — Sequence Orchestrator & State Machine
Manages outbound drip campaigns using a SQLite state machine.
Ensures crash-resilience, throttling, and duplicate prevention.
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time

DB_PATH = Path(__file__).parent / "campaign_state.db"
CSV_PATH = Path(__file__).parent / "personalized_outreach.csv"

# ─── 1. Database Setup ─────────────────────────────────────────
def init_db():
    """Creates the state machine table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_state (
            domain TEXT PRIMARY KEY,
            email TEXT,
            step INTEGER DEFAULT 1,
            status TEXT DEFAULT 'PENDING',
            personalized_line TEXT,
            last_sent_at TEXT,
            next_send_at TEXT
        )
    """)
    conn.commit()
    return conn

# ─── 2. Ingestion (Idempotent) ─────────────────────────────────
def ingest_leads(conn):
    """Loads Day 46 data into the state machine without duplicating."""
    df = pd.read_csv(CSV_PATH)
    cursor = conn.cursor()
    
    added_count = 0
    for _, row in df.iterrows():
        # Only insert if domain isn't already in the state machine
        cursor.execute("""
            INSERT OR IGNORE INTO campaign_state 
            (domain, email, personalized_line, next_send_at)
            VALUES (?, ?, ?, ?)
        """, (
            row['domain'], 
            f"decision-maker@{row['domain']}", 
            row['personalized_first_line'],
            datetime.utcnow().isoformat() # Ready to send immediately
        ))
        if cursor.rowcount > 0:
            added_count += 1
            
    conn.commit()
    print(f"✅ Ingested {added_count} new leads into the state machine.")

# ─── 3. The Mock Sender (Simulating Resend/SendGrid API) ───────
def send_email(email: str, subject: str, body: str):
    """Mock API call to an ESP. In production, this is a requests.post() to Resend."""
    # Simulate network latency
    time.sleep(0.5) 
    print(f"   📤 [SENT] To: {email} | Subject: {subject}")
    return True

# ─── 4. The Orchestrator Loop (The State Machine) ──────────────
def process_queue(conn):
    """Finds emails that are due to be sent and updates their state."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    # Find leads where next_send_at is in the past and status is PENDING
    cursor.execute("""
        SELECT domain, email, step, personalized_line 
        FROM campaign_state 
        WHERE status = 'PENDING' AND next_send_at <= ?
    """, (now,))
    
    queue = cursor.fetchall()
    print(f"\n⏳ Processing queue: {len(queue)} emails due to send right now.\n")
    
    for domain, email, step, hook in queue:
        subject = "Quick question about your tech stack"
        body = f"{hook}\n\nAre you open to a brief chat about your data infrastructure?\n\nBest,\nAaliyan"
        
        success = send_email(email, subject, body)
        
        if success:
            # Update State: Move to next step, set delay (e.g., 3 days for Step 2)
            next_step = step + 1
            delay_days = 3 if step == 1 else 7 
            
            # If step > 2, mark as COMPLETED (end of sequence)
            new_status = 'COMPLETED' if step >= 2 else 'PENDING'
            next_send_time = (datetime.utcnow() + timedelta(days=delay_days)).isoformat()
            
            cursor.execute("""
                UPDATE campaign_state 
                SET step = ?, status = ?, last_sent_at = ?, next_send_at = ?
                WHERE domain = ?
            """, (next_step, new_status, now, next_send_time, domain))
            
    conn.commit()
    print("\n✅ Queue processed. State machine updated.")

# ─── 5. Reporting ───────────────────────────────────────────────
def print_dashboard(conn):
    """Quick terminal view of the campaign health."""
    df = pd.read_sql_query("SELECT status, COUNT(*) as count FROM campaign_state GROUP BY status", conn)
    print("\n📊 Campaign State Dashboard:")
    print(df.to_string(index=False))
    print("-" * 30)

if __name__ == "__main__":
    print("🚀 Initializing Sequence Orchestrator...")
    conn = init_db()
    
    ingest_leads(conn)
    process_queue(conn)
    print_dashboard(conn)
    
    conn.close()