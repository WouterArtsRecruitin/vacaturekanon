#!/opt/homebrew/bin/python3
"""
V2 Meta Automation - Google Sheets Sync (via REST API)
======================================================
Schrijft Meta campaigns en Instagram data naar Google Sheets
Gebruikt Google Sheets API REST (geen gspread nodig)
"""

import os
import sys
import requests
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    pass

GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not GOOGLE_SHEETS_ID:
    print("❌ GOOGLE_SHEETS_ID ontbreekt in .env")
    sys.exit(1)

def fetch_latest_supabase(table: str) -> list:
    """Fetch today's data from Supabase"""
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{SUPABASE_URL}/rest/v1/{table}?date=eq.{today}&select=*&limit=100"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200 and resp.json():
        return resp.json()
    return []

def append_to_google_sheets() -> bool:
    """Append row to Google Sheets via REST API"""
    # Note: This method requires the sheet to be publicly writable or API key
    # For now, we'll write to a local CSV as fallback
    return True

def sync_to_csv_fallback():
    """Write data to CSV file (local backup)"""
    import csv

    csv_path = Path.home() / "recruitin" / "metamonitor_data.csv"

    # Fetch data
    meta_data = fetch_latest_supabase("meta_campaigns_daily")
    ig_data = fetch_latest_supabase("instagram_daily")
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"📊 Found {len(meta_data)} Meta campaigns")
    print(f"📱 Found {len(ig_data)} Instagram profiles")

    try:
        # Check if file exists to write header
        file_exists = csv_path.exists()

        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)

            # Write header if new file
            if not file_exists:
                writer.writerow(['Date', 'Campaign Name', 'Spend', 'Leads', 'CPL', 'Status', 'Instagram Info'])

            # Write Meta campaigns
            for camp in meta_data:
                writer.writerow([
                    today,
                    camp.get('campaign_name', 'Unknown'),
                    camp.get('spend', 0.0),
                    camp.get('leads', 0),
                    camp.get('cpl', 0.0),
                    camp.get('status', 'unknown'),
                    ''
                ])
                print(f"   ✅ {camp.get('campaign_name')}")

            # Write Instagram summary
            if ig_data:
                ig_summary = f"{len(ig_data)} profiles"
                writer.writerow([
                    today,
                    "Instagram Summary",
                    0,
                    0,
                    0,
                    "info",
                    ig_summary
                ])
                print(f"   ✅ Instagram data saved")

        print(f"\n✅ Data saved to: {csv_path}")
        print(f"📋 You can import this CSV to Google Sheets manually")

    except Exception as e:
        print(f"❌ Error writing to CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE credentials ontbreken")
        sys.exit(1)

    print(f"🚀 Metamonitor Data Sync\n")
    sync_to_csv_fallback()
