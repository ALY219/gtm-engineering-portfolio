import sys
import os
import pandas as pd

# Add parent directory to path to import Day 42 client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from integrations.hubspot.hubspot_client import find_by_email, create_contact

HOT_THRESHOLD = 70

def push_hot_leads():
    df = pd.read_csv("enriched_leads.csv")
    hot_leads = df[df['icp_score'] >= HOT_THRESHOLD]
    
    print(f"\n🚀 Pushing {len(hot_leads)} hot leads to HubSpot as SQLs...\n")
    
    for index, row in hot_leads.iterrows():
        domain = row['domain']
        score = row['icp_score']
        reasoning = row['reasoning']
        
        # We only have domains, so we generate a placeholder email for the CRM
        email = f"decision-maker@{domain}"
        
        props = {
            "email": email,
            "company": domain,
            "website": f"https://{domain}",
            "lifecyclestage": "salesqualifiedlead",
            "jobtitle": f"AI ICP Score: {score}/100"  # Hack to make the score visible in the HubSpot UI!
        }
        
        # Use Day 42's idempotency check!
        existing_id = find_by_email(email)
        if existing_id:
            print(f"  ⏭️  {domain} already in HubSpot (ID: {existing_id}). Skipping.")
        else:
            new_id = create_contact(props)
            if new_id:
                print(f"  ✅ Created {domain} (Score: {score}) -> HubSpot ID: {new_id}")
            else:
                print(f"  ❌ Failed to create {domain}")
                
    print("\n✅ Routing complete. Check HubSpot CRM!")

if __name__ == "__main__":
    push_hot_leads()