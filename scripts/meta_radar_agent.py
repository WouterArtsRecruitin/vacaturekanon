#!/opt/homebrew/bin/python3
"""
Meta Radar Agent
================
Automatisch monitoren van concurrenten via de Facebook Ad Library (via Apify).

Setup:
1. Apify API Token in .env (`APIFY_TOKEN`)
2. Slack Webhook in .env (`SLACK_WEBHOOK_URL`)
3. Kies een specifieke Facebook Ad Library Scraper actor uit de Apify Store.
   Bijv: curious_coder~facebook-ads-library-scraper of devX~facebook-ad-scraper.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    print("Kan python-dotenv niet laden.")

# ===== CONFIG =====
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Pas deze Actor ID aan afhankelijk van welke je in Apify kiest
ACTOR_ID = os.getenv("APIFY_META_RADAR_ACTOR", "curious_coder~facebook-ads-library-scraper")
APIFY_BASE = "https://api.apify.com/v2"

# De Facebook Ad Library search URL's van de concurrenten
# Voorbeeld search URL voor Artra:
# https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=NL&q=Artra
START_URLS = [
    {
        "name": "Artra",
        "url": "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=NL&q=Artra"
    }
    # Voeg hier meer URL's toe van concurrenten!
]

HISTORY_FILE = Path.home() / "recruitin" / "meta_radar_history.json"
MAX_ITEMS = 50

def load_history():
    if not HISTORY_FILE.exists():
        return {}
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def _headers():
    return {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json",
    }

def run_scraper(urls):
    print(f"[{datetime.now()}] 🚀 Start Meta Radar Agent via Apify...")
    
    # Input schema verschilt licht per actor, dit is de meest voorkomende structuur:
    payload = {
        "urls": [{"url": u["url"]} for u in urls],
        "maxItems": MAX_ITEMS,
        "country": "NL",
        "activeStatus": "active"
    }
    
    url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs"
    r = requests.post(url, headers=_headers(), json=payload)
    
    if r.status_code not in (200, 201):
        print(f"❌ Fout bij starten actor: HTTP {r.status_code} - {r.text}")
        return None
        
    run_id = r.json()["data"]["id"]
    print(f"   ✅ Actor gestart, Run ID: {run_id}")
    return run_id

def wait_for_run(run_id):
    print("   ⏳ Wachten tot scraper klaar is...")
    url = f"{APIFY_BASE}/actor-runs/{run_id}"
    while True:
        r = requests.get(url, headers=_headers())
        status = r.json()["data"]["status"]
        if status == "SUCCEEDED":
            print("   🎯 Run succesvol afgerond!")
            return True
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"   ❌ Run mislukt met status: {status}")
            return False
        time.sleep(10)

def fetch_results(run_id):
    url = f"{APIFY_BASE}/actor-runs/{run_id}/dataset/items"
    r = requests.get(url, headers=_headers(), params={"clean": "true"})
    if r.status_code == 200:
        return r.json()
    return []

def send_slack_alert(competitor_name, ad):
    """Verstuurt een mooi ingedeeld Slack bericht"""
    if not SLACK_WEBHOOK:
        return
        
    ad_id = ad.get("id", "Onbekend ID")
    body = ad.get("body", "Geen ad tekst gevonden...")[:300]
    link = ad.get("adLibraryUrl") or ad.get("url") or f"https://www.facebook.com/ads/library/?id={ad_id}"
    media_url = ad.get("imageUrl") or ad.get("videoUrl", "")
    
    block_msg = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Meta Radar: {competitor_name} heeft een nieuwe Ad!"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Ad Copy:*\n> {body}...\n\n👉 *<|Link naar advertentie|{link}>*"
                }
            }
        ]
    }
    
    if media_url:
        block_msg["blocks"].append({
            "type": "image",
            "image_url": media_url,
            "alt_text": "Ad Creative"
        })

    requests.post(SLACK_WEBHOOK, json=block_msg)

def log_to_supabase(ad_id, competitor_name, page_name, ad_text, media_url, ad_snapshot_url=""):
    """Log competitor ad to Supabase competitor_ads table"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    data = {
        "ad_id": ad_id,
        "competitor_name": competitor_name,
        "page_name": page_name,
        "ad_text_preview": ad_text[:300] if ad_text else "",
        "media_url": media_url or "",
        "ad_snapshot_url": ad_snapshot_url or "",
        "source": "apify_radar",
        "country": "NL"
    }

    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/competitor_ads",
            json=data,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Prefer": "resolution=merge-duplicates"
            },
            timeout=10
        )
        if r.status_code not in (200, 201):
            print(f"      ⚠️ Supabase error: {r.status_code}")
    except Exception as e:
        print(f"      ⚠️ Supabase log failed: {e}")

if __name__ == "__main__":
    if not APIFY_TOKEN:
        sys.exit("❌ APIFY_TOKEN missend in .env")
        
    history = load_history()
    run_id = run_scraper(START_URLS)
    
    if run_id and wait_for_run(run_id):
        results = fetch_results(run_id)
        print(f"📊 {len(results)} advertenties gevonden.")
        
        new_ads_detected = 0
        for ad in results:
            ad_id = str(ad.get("id", ad.get("adId", "")))
            if not ad_id:
                continue
                
            # Om te bepalen van welke concurrent deze ad was, kijken we in de data:
            page_name = ad.get("pageName", "Onbekend")
            
            # Check of we deze ID al gezien hebben
            if ad_id not in history:
                print(f"   🔥 Nieuwe ad gevonden van {page_name} (ID: {ad_id})")
                ad_text = ad.get("body", "")
                media_url = ad.get("imageUrl") or ad.get("videoUrl", "")
                send_slack_alert(page_name, ad)
                log_to_supabase(ad_id, page_name, page_name, ad_text, media_url)
                history[ad_id] = {
                    "date_discovered": datetime.now().isoformat(),
                    "page": page_name
                }
                new_ads_detected += 1
                
        if new_ads_detected > 0:
            save_history(history)
            print(f"✅ {new_ads_detected} nieuwe ads naar Slack gestuurd en historie bijgewerkt!")
        else:
            print("💤 Geen nieuwe advertenties ontdekt. Alles is up to date.")
