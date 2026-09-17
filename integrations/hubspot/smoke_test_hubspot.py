import os, requests
from dotenv import load_dotenv
load_dotenv()  # reads .env from THIS folder

key = os.getenv("HUBSPOT_SERVICE_KEY")
BASE = "https://api.hubapi.com/crm/v3/objects/contacts"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

payload = {"properties": {"email": "smoke1@growthflowai.site",
                          "firstname": "Smoke", "lastname": "One",
                          "lifecyclestage": "lead"}}

# Test 1: create a contact
r1 = requests.post(BASE, headers=headers, json=payload)
print("CREATE   :", r1.status_code, r1.json().get("id", r1.text[:150]))

# Test 2: same email again -> should be rejected as duplicate
r2 = requests.post(BASE, headers=headers, json=payload)
print("DUPLICATE:", r2.status_code, r2.json().get("message", r2.text[:150]))