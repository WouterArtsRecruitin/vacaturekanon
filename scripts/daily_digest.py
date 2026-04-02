#!/opt/homebrew/bin/python3
"""
Daily Monitoring Digest — Unified Dashboard Summary
===================================================
Consolidates all monitoring data (own campaigns, competitors, topics)
into one Slack message. Run daily at 08:00 to see the full picture.
"""

import os
import json
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

def get_supabase_data(table, days=1, where_clause=""):
    """Fetch data from Supabase table."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    since = (datetime.now() - timedelta(days=days)).isoformat()

    query = f"first_seen.gte.{since}"
    if where_clause:
        query += f"&{where_clause}"

    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}?{query}&order=first_seen.desc",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            },
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"⚠️ Supabase query error: {e}")

    return []

def format_slack_digest(dry_run=False):
    """Build unified Slack Block Kit message."""

    # Fetch all monitoring data for last 24h
    own_campaigns = get_supabase_data("meta_campaigns_daily", days=1)
    competitor_ads = get_supabase_data("competitor_ads", days=1)
    topic_ads = get_supabase_data("topic_monitor_ads", days=1)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📊 DAILY MONITORING DIGEST"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"_Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} — Last 24h activity_"
            }
        },
        {"type": "divider"}
    ]

    # === OWN CAMPAIGNS ===
    if own_campaigns:
        campaign_text = "💰 *EIGEN CAMPAGNES* (gisteren)\n"
        total_spend = 0
        total_leads = 0
        green_count = 0
        yellow_count = 0
        red_count = 0

        for camp in own_campaigns[:5]:  # Top 5
            name = camp.get("campaign_name", "Unknown")
            cpl = camp.get("cpl", 0)
            status_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(camp.get("status", ""), "⚪")
            spend = camp.get("spend", 0)
            leads = camp.get("leads", 0)

            campaign_text += f"  {status_emoji} *{name}*: €{cpl:.2f} CPL | {leads} leads | €{spend:.0f}\n"
            total_spend += spend
            total_leads += leads

            if camp.get("status") == "green":
                green_count += 1
            elif camp.get("status") == "yellow":
                yellow_count += 1
            else:
                red_count += 1

        campaign_text += f"\n  *Total:* €{total_spend:.0f} spend | {total_leads} leads"
        if red_count > 0:
            campaign_text += f" | ⚠️ {red_count} red campaigns"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": campaign_text}
        })
        blocks.append({"type": "divider"})

    # === COMPETITOR ADS ===
    if competitor_ads:
        competitors_grouped = {}
        for ad in competitor_ads:
            comp = ad.get("competitor_name", "Unknown")
            if comp not in competitors_grouped:
                competitors_grouped[comp] = []
            competitors_grouped[comp].append(ad)

        comp_text = "🏆 *COMPETITOR ADS* (24h)\n"
        for comp, ads in sorted(competitors_grouped.items())[:5]:  # Top 5 competitors
            source_map = {"apify_radar": "Radar", "apify_monitor": "Monitor", "meta_api": "API"}
            sources = set(ad.get("source", "unknown") for ad in ads)
            source_str = ", ".join([source_map.get(s, s) for s in sources])
            comp_text += f"  • *{comp}*: {len(ads)} new ads ({source_str})\n"

        total_new = sum(len(ads) for ads in competitors_grouped.values())
        comp_text += f"\n  _Total: {total_new} new competitor ads_"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": comp_text}
        })
        blocks.append({"type": "divider"})

    # === TOPIC ALERTS ===
    if topic_ads:
        topics_grouped = {}
        for ad in topic_ads:
            cat = ad.get("category", "Unknown")
            if cat not in topics_grouped:
                topics_grouped[cat] = []
            topics_grouped[cat].append(ad)

        topic_text = "📥 *TOPIC ALERTS* (24h)\n"
        for cat, ads in sorted(topics_grouped.items())[:5]:  # Top 5 topics
            unique_pages = len(set(ad.get("page_id") for ad in ads))
            topic_text += f"  • *{cat}*: {len(ads)} ads from {unique_pages} advertiser(s)\n"

        total_topic_ads = sum(len(ads) for ads in topics_grouped.values())
        topic_text += f"\n  _Total: {total_topic_ads} topic-related ads discovered_"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": topic_text}
        })

    # === FOOTER ===
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"_Daily Digest — Recruitin B.V. | All monitoring integrated into Supabase_"
        }]
    })

    payload = {
        "text": "📊 Daily Monitoring Digest",
        "blocks": blocks
    }

    return payload

def send_slack(payload, dry_run=False):
    """Send or print payload."""
    if dry_run:
        print("\n🔵 DRY RUN — Slack payload:\n")
        print(json.dumps(payload, indent=2))
        return

    if not SLACK_WEBHOOK:
        print("⚠️ SLACK_WEBHOOK_URL not set")
        return

    try:
        r = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Digest sent to Slack!")
        else:
            print(f"⚠️ Slack returned {r.status_code}")
    except Exception as e:
        print(f"❌ Slack error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Daily Monitoring Digest")
    parser.add_argument("--dry-run", action="store_true", help="Print payload, don't send")
    parser.add_argument("--days", type=int, default=1, help="Days to look back (default: 1)")

    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] Generating Daily Digest...")

    payload = format_slack_digest(dry_run=args.dry_run)
    send_slack(payload, dry_run=args.dry_run)

    print("Done!")

if __name__ == "__main__":
    main()
