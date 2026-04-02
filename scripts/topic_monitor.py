#!/opt/homebrew/bin/python3
"""
Topic Monitor — Recruitment Topic Tracking via Meta Ad Library API
==================================================================
Monitort recruitment-gerelateerde topics in Meta Ads per categorie
(vacaturetekst, employer branding, whitepapers, etc.) en stuurt
Slack alerts wanneer nieuwe advertenties voor die topics gevonden worden.

Gebruikt Meta Ad Library API — geen Apify actor nodig, gratis en officieel.
"""

import os
import sys
import json
import csv
import argparse
import hashlib
import requests
import time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    pass

# ===== CREDENTIALS =====
META_TOKEN = os.getenv("META_ACCESS_TOKEN")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ===== API CONFIG =====
API_VERSION = "v21.0"
AD_LIBRARY_URL = f"https://graph.facebook.com/{API_VERSION}/ads_archive"

# ===== FILE PATHS =====
TOPICS_CSV = Path.home() / "recruitin" / "topics.csv"
STATE_FILE = Path.home() / "recruitin" / "topic_monitor_state.json"
LOG_FILE = Path("/tmp") / "topic_monitor.log"

def log(msg):
    """Schrijf naar stdout + logfile"""
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def load_topics(category_filter=None):
    """Laad topics uit CSV. Optioneel filteren op categorie."""
    if not TOPICS_CSV.exists():
        log(f"❌ {TOPICS_CSV} niet gevonden!")
        return []

    topics = []
    with open(TOPICS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("category"):
                continue

            # Filter op categorie als opgegeven
            if category_filter and row["category"] not in category_filter:
                continue

            # Parse keywords string naar list
            keywords = []
            if row.get("search_keywords"):
                keywords = [kw.strip() for kw in row["search_keywords"].split(",")]

            topics.append({
                "category": row["category"],
                "emoji": row.get("emoji", "📰"),
                "slack_prefix": row.get("slack_prefix", "TOPIC"),
                "search_keywords": keywords,
                "alert_threshold": int(row.get("alert_threshold", 1))
            })

    log(f"✅ Geladen {len(topics)} topics van {TOPICS_CSV.name}")
    return topics

def load_state():
    """Laad dedup state file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"last_run": None, "ads": {}}

def save_state(state):
    """Sla state op met timestamp."""
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def create_ad_hash(ad_data):
    """Genereer MD5 hash van ad content (fingerprint)"""
    text = (ad_data.get("ad_creative_bodies", [""])[0] if ad_data.get("ad_creative_bodies") else "")
    page_id = ad_data.get("page_id", "")

    content = f"{text[:200]}|{page_id}"
    return hashlib.md5(content.encode()).hexdigest()[:8]

def is_new_ad(category, ad_id, ad_hash, state):
    """Check of ad echt nieuw is (exact ID + 7-dag hash window)"""
    if category not in state["ads"]:
        return True

    cat_state = state["ads"][category]

    # Exacte ID match = zeker duplicate
    if ad_id in cat_state:
        return False

    # 7-dag near-duplicate check (zelfde hash = waarschijnlijk variant)
    page_id = state["ads"].get(category, {}).get(ad_id, {}).get("page_id")

    for stored_id, stored_info in cat_state.items():
        if stored_info.get("hash") == ad_hash and stored_info.get("page_id") == page_id:
            first_seen = stored_info.get("first_seen", "")
            if first_seen:
                try:
                    days_old = (datetime.now() - datetime.fromisoformat(first_seen)).days
                    if days_old < 7:
                        return False  # Near-duplicate within 7 days
                except:
                    pass

    return True

def search_ads_archive(keyword, country="NL", max_pages=3):
    """Roep Meta Ad Library API aan. Paginatie via cursor."""
    if not META_TOKEN:
        log("❌ META_ACCESS_TOKEN missing!")
        return []

    results = []
    params = {
        "access_token": META_TOKEN,
        "ad_reached_countries": json.dumps([country]),
        "ad_active_status": "ACTIVE",
        "search_terms": keyword,
        "fields": "id,ad_creative_bodies,ad_creative_link_titles,page_name,page_id,ad_delivery_start_time,ad_snapshot_url",
        "limit": 50
    }

    page_count = 0
    next_cursor = None

    while page_count < max_pages:
        if next_cursor:
            params["after"] = next_cursor

        try:
            r = requests.get(AD_LIBRARY_URL, params=params, timeout=30)

            if r.status_code != 200:
                error_data = r.json()
                error_code = error_data.get("error", {}).get("code")
                error_msg = error_data.get("error", {}).get("message", "Unknown error")

                # Special handling for token expiry
                if error_code == 190:
                    log(f"❌ TOKEN EXPIRED (error 190): {error_msg}")
                    send_slack_error("⚠️ META TOKEN EXPIRED",
                        f"The META_ACCESS_TOKEN in .env has expired.\nError: {error_msg}\nGenerated ~2026-05-04.")

                return results

            data = r.json()

            # Collect ads from this page
            if "data" in data:
                results.extend(data["data"])
                page_count += 1

            # Check for next page
            paging = data.get("paging", {})
            next_cursor = paging.get("cursors", {}).get("after")
            if not next_cursor:
                break

            time.sleep(1)  # Rate limiting

        except Exception as e:
            log(f"⚠️ API error for keyword '{keyword}': {str(e)}")
            break

    return results

def process_category(topic, state, dry_run=False):
    """Laad ads voor 1 categorie. Return: list van nieuwe ads."""
    category = topic["category"]
    keywords = topic["search_keywords"]

    if category not in state["ads"]:
        state["ads"][category] = {}

    new_ads = []
    seen_ads_in_run = set()  # Dedup within this run (same keyword might match multiple times)

    for keyword in keywords:
        log(f"   🔍 {category}: searching '{keyword}'...")
        ads = search_ads_archive(keyword, max_pages=3)

        for ad in ads:
            ad_id = ad.get("id")
            if not ad_id:
                continue

            ad_id = str(ad_id)

            # Skip if we've already flagged this in this run
            if ad_id in seen_ads_in_run:
                continue

            ad_hash = create_ad_hash(ad)

            # Check if truly new
            if not is_new_ad(category, ad_id, ad_hash, state):
                continue

            # NEW AD DETECTED
            seen_ads_in_run.add(ad_id)

            ad_entry = {
                "hash": ad_hash,
                "first_seen": datetime.now().isoformat(),
                "page_name": ad.get("page_name", "Unknown"),
                "page_id": ad.get("page_id", ""),
                "keyword_matched": keyword,
                "text_preview": (ad.get("ad_creative_bodies", [""])[0] if ad.get("ad_creative_bodies") else "")[:300],
                "ad_snapshot_url": ad.get("ad_snapshot_url", ""),
                "ad_delivery_start_time": ad.get("ad_delivery_start_time", "")
            }

            state["ads"][category][ad_id] = ad_entry
            new_ads.append((ad_id, ad_entry))

            log(f"      🚨 NEW: {ad_entry['page_name']} | {keyword}")

    return new_ads

def format_slack_message(topic, new_ads):
    """Build Slack Block Kit message for a topic category."""
    emoji = topic["emoji"]
    prefix = topic["slack_prefix"]
    category = topic["category"]

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {prefix} — {len(new_ads)} nieuwe advertentie(s)"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} | 🌍 Meta Ad Library NL"
            }
        },
        {"type": "divider"}
    ]

    # Add per-ad sections (max 10 to avoid Slack limits)
    for ad_id, ad_info in new_ads[:10]:
        page_name = ad_info["page_name"]
        keyword = ad_info["keyword_matched"]
        text = ad_info["text_preview"]
        url = ad_info["ad_snapshot_url"]
        start_date = ad_info["ad_delivery_start_time"]

        ad_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"""🏢 *{page_name}* | 🔑 `{keyword}`
📣 {text}{"..." if len(text) > 200 else ""}
📅 Live seit: {start_date[:10] if start_date else "Unknown"}"""
            }
        }

        blocks.append(ad_block)

        if url:
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"<{url}|Bekijk advertentie in Ad Library>"
                }]
            })

        blocks.append({"type": "divider"})

    # Footer
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"_Topic Monitor — Recruitin B.V. | {datetime.now().strftime('%H:%M')} | Meta Ad Library API_"
        }]
    })

    return {
        "text": f"{emoji} {len(new_ads)} neue {category} ads",
        "blocks": blocks
    }

def send_slack_alert(payload, dry_run=False):
    """POST payload naar Slack webhook."""
    if not SLACK_WEBHOOK:
        return

    if dry_run:
        log(f"\n🔵 DRY RUN — Slack payload:\n{json.dumps(payload, indent=2)}\n")
        return

    try:
        r = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
        if r.status_code == 200:
            log("   ✅ Slack alert sent")
        else:
            log(f"   ⚠️ Slack returned {r.status_code}")
    except Exception as e:
        log(f"   ❌ Slack error: {e}")

def send_slack_error(title, msg):
    """Send error alert to Slack."""
    if not SLACK_WEBHOOK:
        return

    payload = {
        "text": title,
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": title}},
            {"type": "section", "text": {"type": "mrkdwn", "text": msg}}
        ]
    }

    try:
        requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
    except:
        pass

def log_to_supabase(category, ad_id, ad_info):
    """Log ad to Supabase table `topic_monitor_ads`"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    data = {
        "ad_archive_id": ad_id,
        "category": category,
        "keyword_matched": ad_info.get("keyword_matched"),
        "page_name": ad_info.get("page_name"),
        "page_id": ad_info.get("page_id"),
        "ad_text_preview": ad_info.get("text_preview"),
        "ad_snapshot_url": ad_info.get("ad_snapshot_url"),
        "ad_delivery_start_time": ad_info.get("ad_delivery_start_time"),
        "country": "NL"
    }

    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/topic_monitor_ads",
            json=data,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Prefer": "resolution=merge-duplicates"
            },
            timeout=10
        )
        if r.status_code not in (200, 201):
            log(f"      ⚠️ Supabase error: {r.status_code}")
    except Exception as e:
        log(f"      ⚠️ Supabase log failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Recruitment Topic Monitor")
    parser.add_argument("--dry-run", action="store_true", help="Print Slack, don't send")
    parser.add_argument("--category", action="append", help="Run only this category (repeatable)")
    parser.add_argument("--country", default="NL", help="Country code (NL, BE, DE)")
    parser.add_argument("--max-pages", type=int, default=3, help="Max API pages per keyword")
    parser.add_argument("--reset-state", action="store_true", help="Wipe state file")

    args = parser.parse_args()

    log(f"\n{'='*60}")
    log(f"Topic Monitor v1.0 START")
    log(f"{'='*60}")

    # Reset state if requested
    if args.reset_state:
        STATE_FILE.unlink(missing_ok=True)
        log("✅ State file wiped")

    # Load topics
    category_filter = args.category if args.category else None
    topics = load_topics(category_filter=category_filter)

    if not topics:
        log("❌ No topics loaded. Exiting.")
        return

    # Load state
    state = load_state()

    # Process each topic
    total_new_ads = 0
    topics_with_alerts = 0

    for topic in topics:
        category = topic["category"]
        log(f"\n📍 Category: {category}")

        new_ads = process_category(topic, state, dry_run=args.dry_run)

        if len(new_ads) >= topic["alert_threshold"]:
            log(f"   📊 {len(new_ads)} ads meet alert threshold")

            # Send Slack alert
            payload = format_slack_message(topic, new_ads)
            send_slack_alert(payload, dry_run=args.dry_run)

            # Log to Supabase
            for ad_id, ad_info in new_ads:
                log_to_supabase(category, ad_id, ad_info)

            total_new_ads += len(new_ads)
            topics_with_alerts += 1
        else:
            log(f"   💤 Below threshold ({len(new_ads)} < {topic['alert_threshold']})")

    # Save state
    if not args.dry_run:
        save_state(state)

    # Summary
    log(f"\n{'='*60}")
    log(f"COMPLETE: {total_new_ads} new ads found across {topics_with_alerts} topics")
    log(f"{'='*60}\n")

if __name__ == "__main__":
    main()
