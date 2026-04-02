#!/opt/homebrew/bin/python3
"""
V2 Meta Automation - Monitor Agent (Direct to Google Sheets)
============================================================
Haalt Meta campaign data op en schrijft DIRECT naar Google Sheets.
Geen Supabase meer nodig!
"""

import os
import sys
import csv
import requests
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    print("Kan python-dotenv niet laden.")

META_TOKEN = os.getenv("META_ACCESS_TOKEN")
# Support multiple accounts: META_ACCOUNT_ID or META_ACCOUNT_IDS (comma-separated)
META_ACCOUNTS_STR = os.getenv("META_ACCOUNT_IDS") or os.getenv("META_ACCOUNT_ID") or os.getenv("META_AD_ACCOUNT_ID")
META_ACCOUNTS = [acc.strip() for acc in META_ACCOUNTS_STR.split(",")] if META_ACCOUNTS_STR else []
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")

API_VERSION = "v21.0"
CSV_PATH = Path.home() / "recruitin" / "metamonitor_data.csv"

def get_meta_campaign_insights(account_id: str) -> list:
    """Fetch Meta insights for a specific account"""
    url = f"https://graph.facebook.com/{API_VERSION}/{account_id}/insights"

    params = {
        "access_token": META_TOKEN,
        "date_preset": "yesterday",
        "level": "campaign",
        "fields": "campaign_id,campaign_name,impressions,clicks,spend,actions"
    }

    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"❌ Meta API error for {account_id}: {resp.text}")
        return []

    data = resp.json().get("data", [])
    return data

def process_campaigns(insights: list) -> list:
    """Process campaign data and return rows for Google Sheets"""
    today = datetime.now().strftime("%Y-%m-%d")
    high_cpl_alerts = []
    rows = []

    for row in insights:
        spend = float(row.get("spend", 0.0))
        name = row.get("campaign_name", "Unknown")

        # Extract leads from actions
        leads = 0
        actions = row.get("actions", [])
        for action in actions:
            if action.get("action_type") in ("lead", "onsite_conversion.lead"):
                leads += int(action.get("value", 0))

        cpl = round((spend / leads), 2) if leads > 0 else spend

        status = "🟢"  # Green
        if cpl > 65.0:
            status = "🔴"  # Red
            high_cpl_alerts.append((name, cpl, spend))
        elif cpl > 35.0:
            status = "🟡"  # Yellow

        # Row for Google Sheets
        rows.append([
            today,
            name,
            round(spend, 2),
            leads,
            round(cpl, 2),
            status,
            ""
        ])

    return rows, high_cpl_alerts

def append_to_csv(rows: list):
    """Append rows to CSV file"""
    print("💾 Saving to CSV...")

    # Check if file exists
    file_exists = CSV_PATH.exists()

    with open(CSV_PATH, 'a', newline='') as f:
        writer = csv.writer(f)

        # Write header if new file
        if not file_exists:
            writer.writerow([
                'Date', 'Campaign Name', 'Spend', 'Leads', 'CPL', 'Status', 'Instagram Info'
            ])

        # Write rows
        for row in rows:
            writer.writerow(row)
            print(f"   ✅ {row[1]} (€{row[2]} spend, CPL: €{row[4]})")

    print(f"📊 Data saved to: {CSV_PATH}")

def send_slack_alerts(alerts: list):
    """Send Slack alerts for high CPL campaigns"""
    if not SLACK_WEBHOOK or not alerts:
        print("   No critical alerts to send.")
        return

    msg = "🔴 *HIGH CPL ALERTS* 🔴\n\n"
    for name, cpl, spend in alerts:
        msg += f"⚠️ *{name}*: CPL = €{cpl} (Spend: €{spend}). Threshold > €65.\n"
        msg += "👉 _Consider pausing or rotating creatives._\n\n"

    requests.post(SLACK_WEBHOOK, json={"text": msg})
    print("🚨 Slack alerts sent!")

if __name__ == "__main__":
    print(f"[{datetime.now()}] Start Meta Monitor Agent (Multiple Accounts)...\n")

    if not META_TOKEN or not META_ACCOUNTS:
        print("❌ Missing credentials (META_ACCESS_TOKEN or META_ACCOUNT_IDS). Check .env")
        print("\nSetup multiple accounts:")
        print("   echo 'META_ACCOUNT_IDS=account1,account2,account3' >> ~/.env/recruitin/.env")
        sys.exit(1)

    if not GOOGLE_SHEETS_ID:
        print("❌ GOOGLE_SHEETS_ID missing. Check .env")
        sys.exit(1)

    print(f"📊 Monitoring {len(META_ACCOUNTS)} account(s):\n")
    all_rows = []
    all_alerts = []

    # Fetch from all accounts
    for account_id in META_ACCOUNTS:
        print(f"📈 Fetching {account_id}...")
        insights = get_meta_campaign_insights(account_id)
        if insights:
            rows, alerts = process_campaigns(insights)
            all_rows.extend(rows)
            all_alerts.extend(alerts)
            print(f"   ✅ Found {len(insights)} campaigns\n")
        else:
            print(f"   ⚠️ No data found\n")

    # Save to CSV
    if all_rows:
        append_to_csv(all_rows)
        send_slack_alerts(all_alerts)
    else:
        print("⚠️ No campaign data found in any account.")

    print("🎉 Monitoring run complete!")
