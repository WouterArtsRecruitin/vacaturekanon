#!/opt/homebrew/bin/python3
"""
V2.1 Meta Automation - Competitor Ad Monitor (CSV + Smart Duplication)
=======================================================================
Scraapt actieve Facebook Ads van concurrenten via Apify. 
Ondersteunt CSV import van competitors en slimme duplicate detection.
"""

import os
import sys
import json
import time
import csv
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Laad credentials
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    pass

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "apify~facebook-ads-scraper")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SEEN_ADS_FILE = Path.home() / "recruitin" / "apify_seen_ads.json"
COMPETITORS_CSV = Path.home() / "recruitin" / "competitors.csv"

def load_competitors_from_csv() -> list:
    """Laad competitors uit CSV met kolommen: name, url, keywords (optioneel)"""
    competitors = []
    if COMPETITORS_CSV.exists():
        with open(COMPETITORS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("name") and row.get("url"):
                    keywords = []
                    if row.get("keywords"):
                        keywords = [kw.strip() for kw in row["keywords"].split(",")]
                    competitors.append({
                        "name": row["name"],
                        "url": row["url"],
                        "keywords": keywords,
                        "last_check": None
                    })
        print(f"✅ Geladen {len(competitors)} competitors uit {COMPETITORS_CSV.name}")
        return competitors
    else:
        print(f"⚠️  CSV niet gevonden: {COMPETITORS_CSV}")
        print("   Maak competitors.csv met kolommen: name,url,keywords")
        return []

def create_ad_hash(ad_data: dict) -> str:
    """Genereer hash van ad content (detecteert dubbels + wijzigingen)"""
    text = ad_data.get("text", "") or ad_data.get("body", "")
    image = ad_data.get("imageUrl", "") or ad_data.get("mediaUrl", "")
    
    # Hash op basis van tekst + afbeelding (detecteert copy-paste variaties)
    content = f"{text[:200]}|{image[:100]}"
    return hashlib.md5(content.encode()).hexdigest()[:8]

def load_seen_ads() -> dict:
    """Laad eerder geziene ads met metadata"""
    if SEEN_ADS_FILE.exists():
        with open(SEEN_ADS_FILE, "r") as f:
            try:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
            except:
                return {}
    return {}

def save_seen_ads(seen_ads: dict):
    """Sla ads op met timestamp en hash"""
    with open(SEEN_ADS_FILE, "w") as f:
        json.dump(seen_ads, f, indent=2)

def filter_by_keywords(ad_text: str, keywords: list) -> bool:
    """Check of ad tekst keywords bevat (case-insensitive)"""
    if not keywords:
        return True  # Geen filter = alles toestaan
    
    text_lower = ad_text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def is_duplicate(ad_id: str, ad_hash: str, competitor: str, seen_ads: dict) -> bool:
    """Check op exacte duplicaten en near-duplicates"""
    comp_data = seen_ads.get(competitor, {})
    
    # Exacte ID match
    if ad_id in comp_data:
        return True
    
    # Near-duplicate: zelfde hash binnen 3 dagen = waarschijnlijk variant
    for stored_id, stored_info in comp_data.items():
        if stored_info.get("hash") == ad_hash:
            stored_date = datetime.fromisoformat(stored_info.get("first_seen", ""))
            if (datetime.now() - stored_date).days < 3:
                return True
    
    return False

def trigger_apify(competitor_name, page_url) -> str:
    """Start Apify actor run"""
    print(f"🚀 Triggering Ad Scraper voor {competitor_name}...")
    
    url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs"
    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "startUrls": [{"url": page_url}],
        "maxItems": 30
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code in (200, 201):
        run_id = response.json()["data"]["id"]
        print(f"   ✅ Run ID: {run_id}")
        return run_id
    else:
        print(f"   ❌ Error: {response.text}")
        return None

def wait_for_data(run_id: str) -> str:
    """Wacht op Apify run completion"""
    print(f"   ⏳ Waiting... ", end="", flush=True)
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    max_wait = 90  # 90 seconden max
    elapsed = 0
    
    while elapsed < max_wait:
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        resp = requests.get(status_url, headers=headers)
        
        if resp.status_code == 200:
            status = resp.json()["data"]["status"]
            if status == "SUCCEEDED":
                dataset_id = resp.json()["data"]["defaultDatasetId"]
                print(f"✅ Dataset: {dataset_id}")
                return dataset_id
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                print(f"❌ Status: {status}")
                return None
            else:
                print(".", end="", flush=True)
        
        time.sleep(10)
        elapsed += 10
    
    print("⏱️ Timeout")
    return None

def fetch_dataset(dataset_id: str) -> list:
    """Haal ads op uit Apify dataset"""
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    resp = requests.get(url, params={"clean": "true", "format": "json"})
    return resp.json() if resp.status_code == 200 else []

def send_slack_alert(competitor, ad_id, ad_text, media_url, ad_type="new"):
    """Stuur Slack notification"""
    if not SLACK_WEBHOOK:
        return
    
    emoji = "🆕" if ad_type == "new" else "🔄"
    msg = f"{emoji} *{competitor}* — {ad_type.upper()}\n\n"
    msg += f"*Copy:* ```{ad_text[:250]}...```\n"
    if media_url:
        msg += f"🖼️ {media_url}\n"
    
    requests.post(SLACK_WEBHOOK, json={"text": msg})

def log_to_supabase(ad_id, competitor_name, page_name, ad_text, media_url):
    """Log competitor ad to Supabase competitor_ads table"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    data = {
        "ad_id": ad_id,
        "competitor_name": competitor_name,
        "page_name": page_name,
        "ad_text_preview": ad_text[:300] if ad_text else "",
        "media_url": media_url or "",
        "source": "apify_monitor",
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

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Competitor Monitor V2 Start\n")
    
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN missing!")
        sys.exit(1)
    
    # Laad competitors
    competitors = load_competitors_from_csv()
    if not competitors:
        print("❌ Geen competitors geladen. Stop.")
        sys.exit(1)
    
    seen_ads = load_seen_ads()
    new_ads_count = 0
    updated_ads_count = 0
    
    for comp in competitors:
        print(f"\n━━━ {comp['name']} ━━━")
        
        run_id = trigger_apify(comp["name"], comp["url"])
        if not run_id:
            continue
        
        time.sleep(2)  # Rate limit
        dataset_id = wait_for_data(run_id)
        if not dataset_id:
            continue
        
        items = fetch_dataset(dataset_id)
        print(f"   📦 Found {len(items)} ads")
        
        # Init competitor in seen_ads
        if comp["name"] not in seen_ads:
            seen_ads[comp["name"]] = {}
        
        comp_seen = seen_ads[comp["name"]]
        
        for item in items:
            ad_id = item.get("id") or item.get("adId") or item.get("adArchiveId")
            if not ad_id:
                continue
            
            ad_id = str(ad_id)
            ad_text = item.get("text", item.get("body", ""))
            
            # Filter op keywords
            if not filter_by_keywords(ad_text, comp.get("keywords", [])):
                continue
            
            # Duplicate check
            ad_hash = create_ad_hash(item)
            if is_duplicate(ad_id, ad_hash, comp["name"], seen_ads):
                continue
            
            # NIEUWE AD!
            media_url = item.get("imageUrl") or item.get("videoUrl") or ""
            page_name = item.get("pageName", comp["name"])
            print(f"   🚨 NEW: {ad_text[:60]}...")

            send_slack_alert(comp["name"], ad_id, ad_text, media_url, "new")
            log_to_supabase(ad_id, comp["name"], page_name, ad_text, media_url)

            comp_seen[ad_id] = {
                "hash": ad_hash,
                "first_seen": datetime.now().isoformat(),
                "text": ad_text[:300]
            }
            new_ads_count += 1
        
        print(f"   ✅ Total tracked: {len(comp_seen)} ads")
        time.sleep(5)  # Rate limiting tussen competitors
    
    save_seen_ads(seen_ads)
    print(f"\n🎉 Complete. {new_ads_count} new ads found!")

if __name__ == "__main__":
    main()
