import os, requests, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/.env", override=True)
TOKEN = os.getenv("META_ACCESS_TOKEN")
ACCOUNT = os.getenv("META_ACCOUNT_ID")
PIXEL = os.getenv("META_PIXEL_ID")

target = {
    "geo_locations": {
        "regions": [
            {"key": "513"},   # Gelderland
            {"key": "514"},   # Overijssel
            {"key": "523"},   # Noord-Brabant
            {"key": "521"},   # Noord-Holland
            {"key": "522"},   # Zuid-Holland
        ],
    },
    "age_min": 28,
    "age_max": 62,
    "flexible_spec": [{
        "job_title": [
            {"id": "103285036402772", "name": "HR Manager"},
            {"id": "105763682788297", "name": "HR Director"},
            {"id": "102374656463855", "name": "Chief Executive Officer"},
            {"id": "108136692547642", "name": "Operations Manager"},
            {"id": "132356540153",    "name": "General Manager"},
        ],
    }],
}

payload = {
    "name": "TEST_ADSET_PROSPECTING",
    "campaign_id": "120245444549340536",
    "daily_budget": "1000",
    "billing_event": "IMPRESSIONS",
    "optimization_goal": "OFFSITE_CONVERSIONS",
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    "promoted_object": json.dumps({"pixel_id": PIXEL, "custom_event_type": "LEAD"}),
    "targeting": json.dumps(target),
    "status": "PAUSED",
    "access_token": TOKEN
}
r = requests.post(f"https://graph.facebook.com/v21.0/{ACCOUNT}/adsets", data=payload)
print(json.dumps(r.json(), indent=2))
