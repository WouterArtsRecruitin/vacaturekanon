#!/opt/homebrew/bin/python3
"""
V2 Meta Automation - Apify IG Sync (Direct to CSV)
==================================================
Scrapes Instagram profiles via Apify and saves DIRECTLY to CSV.
No Supabase needed!
"""

import os
import sys
import csv
import time
import requests
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    print("Kan python-dotenv niet laden.")

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "apify~instagram-profile-scraper")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

CSV_PATH = Path.home() / "recruitin" / "metamonitor_data.csv"

PROFILES = [
    "https://www.instagram.com/recruitinbv/",
    "https://www.instagram.com/markitect_nl/",
    "https://www.instagram.com/other_recruiter/"
]

def trigger_apify() -> str:
    """Trigger Apify Instagram scraper"""
    print(f"🚀 Triggering Apify ID '{APIFY_ACTOR_ID}'...")

    if "~" in APIFY_ACTOR_ID:
        url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs"
    else:
        url = f"https://api.apify.com/v2/actor-tasks/{APIFY_ACTOR_ID}/runs"

    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json"
    }

    usernames = [p.replace("https://www.instagram.com/", "").rstrip("/") for p in PROFILES]

    payload = {
        "usernames": usernames,
        "resultsType": "details",
        "includeFollowers": True,
        "includeEngagementRate": True
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code in (200, 201):
        run_id = response.json()["data"]["id"]
        print(f"✅ Actor started! Run ID: {run_id}")
        return run_id
    else:
        print(f"❌ Error starting actor: {response.text}")
        sys.exit(1)

def wait_for_data(run_id: str) -> str:
    """Wait for Apify run to complete"""
    print(f"⏳ Waiting for data from Apify run {run_id}...")
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}

    while True:
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        resp = requests.get(status_url, headers=headers)
        if resp.status_code == 200:
            status = resp.json()["data"]["status"]
            if status == "SUCCEEDED":
                dataset_id = resp.json()["data"]["defaultDatasetId"]
                print(f"✅ Run completed! Dataset ID: {dataset_id}")
                return dataset_id
            elif status in ("FAILED", "ABORTED"):
                print(f"❌ Apify run failed with status {status}.")
                sys.exit(1)
            else:
                print(f"   Status = {status}. Waiting 10 seconds...")
        time.sleep(10)

def fetch_dataset(dataset_id: str) -> list:
    """Fetch results from Apify dataset"""
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    resp = requests.get(url, params={"clean": "true", "format": "json"})
    return resp.json()

def save_to_csv(data_items: list) -> list:
    """Save Instagram data to CSV file"""
    print("💾 Saving to CSV...")

    today = datetime.now().strftime("%Y-%m-%d")
    file_exists = CSV_PATH.exists()
    saved_handles = []

    with open(CSV_PATH, 'a', newline='') as f:
        writer = csv.writer(f)

        # Write header if new file
        if not file_exists:
            writer.writerow([
                'Date', 'Campaign Name', 'Spend', 'Leads', 'CPL', 'Status', 'Instagram Info'
            ])

        # Process each Instagram profile
        for item in data_items:
            handle = item.get("username", "")
            followers = item.get("followersCount", 0)
            posts = item.get("postsCount", 0)

            # Save as Instagram row
            ig_info = f"{handle}: {followers:,} followers, {posts} posts"
            writer.writerow([
                today,
                f"Instagram: {handle}",
                0,
                0,
                0,
                "📱",
                ig_info
            ])
            saved_handles.append(handle)
            print(f"   ✅ {handle} ({followers:,} followers)")

    return saved_handles

def send_slack_alert(handles: list):
    """Send Slack notification"""
    if not SLACK_WEBHOOK or not handles:
        return

    msg = f"📊 *Instagram Sync Complete*\nSaved to CSV: {', '.join(handles)}"
    requests.post(SLACK_WEBHOOK, json={"text": msg})
    print("✅ Slack notification sent.")

if __name__ == "__main__":
    print(f"[{datetime.now()}] Start V2 Apify IG Sync (Direct to CSV)...\n")

    if not APIFY_TOKEN:
        print("❌ Missing APIFY_TOKEN. Check .env")
        sys.exit(1)

    run_id = trigger_apify()
    dataset_id = wait_for_data(run_id)
    items = fetch_dataset(dataset_id)
    saved = save_to_csv(items)
    send_slack_alert(saved)
    print("🎉 Sync Complete!")
