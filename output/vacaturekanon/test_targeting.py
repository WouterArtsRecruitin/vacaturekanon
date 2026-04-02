import os, requests, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/.env", override=True)
TOKEN = os.getenv("META_ACCESS_TOKEN")
ACCOUNT = os.getenv("META_ACCOUNT_ID")
PIXEL = os.getenv("META_PIXEL_ID")

def test_payload(target_desc, targeting):
    payload = {
        "name": f"TEST_ADSET_{target_desc}",
        "campaign_id": "120245444549340536",
        "daily_budget": "1000",
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "promoted_object": json.dumps({"pixel_id": PIXEL, "custom_event_type": "LEAD"}),
        "targeting": json.dumps(targeting),
        "status": "PAUSED",
        "access_token": TOKEN
    }
    r = requests.post(f"https://graph.facebook.com/v21.0/{ACCOUNT}/adsets", data=payload)
    result = r.json()
    if "error" in result:
        print(f"❌ {target_desc} FAILED: {result['error'].get('message')} - {result['error'].get('error_user_msg')}")
    else:
        print(f"✅ {target_desc} SUCCEEDED: {result['id']}")

# 1. Alleen leeftijd (zoals Lookalike die lukte)
test_payload("Age_Only", {"age_min": 28, "age_max": 62, "geo_locations": {"countries": ["NL"]}})

# 2. Leeftijd + Regios (zonder countries string trickery)
test_payload("Regions", {
    "age_min": 28, "age_max": 62,
    "geo_locations": {
        "regions": [
            {"key": "513"}, {"key": "514"}, {"key": "523"}, {"key": "521"}, {"key": "522"}
        ]
    }
})

# 3. Leeftijd + Countries + Job Titles
test_payload("Job_Titles", {
    "age_min": 28, "age_max": 62,
    "geo_locations": {"countries": ["NL"]},
    "flexible_spec": [{
        "job_title": [
            {"id": "103285036402772", "name": "HR Manager"},
            {"id": "105763682788297", "name": "HR Director"},
            {"id": "102374656463855", "name": "Chief Executive Officer"},
            {"id": "108136692547642", "name": "Operations Manager"},
            {"id": "132356540153", "name": "General Manager"}
        ]
    }]
})
