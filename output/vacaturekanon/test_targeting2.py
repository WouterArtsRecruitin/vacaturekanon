import os, requests, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/.env", override=True)
TOKEN = os.getenv("META_ACCESS_TOKEN")
ACCOUNT = os.getenv("META_ACCOUNT_ID")
PIXEL = os.getenv("META_PIXEL_ID")

payload = {
    "name": "TEST_ADSET_JOBTITLES",
    "campaign_id": "120245444549340536",
    "daily_budget": "1000",
    "billing_event": "IMPRESSIONS",
    "optimization_goal": "OFFSITE_CONVERSIONS",
    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    "promoted_object": json.dumps({"pixel_id": PIXEL, "custom_event_type": "LEAD"}),
    "targeting": json.dumps({
        "age_min": 28, "age_max": 62,
        "geo_locations": {"countries": ["NL"]},
        "targeting_automation": {"advantage_audience": 0},
        "flexible_spec": [{
            "job_title": [
                {"id": "103285036402772", "name": "HR Manager"}
            ]
        }]
    }),
    "status": "PAUSED",
    "access_token": TOKEN
}
r = requests.post(f"https://graph.facebook.com/v21.0/{ACCOUNT}/adsets", data=payload)
print(json.dumps(r.json(), indent=2))
