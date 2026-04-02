#!/opt/homebrew/bin/python3
"""
V2 Meta Automation - Notion Dashboard Sync
==========================================
Haalt de laatst gemaakte Supabase records op (van Vandaag)
en schiet ze naar het Wouter Arts Notion Dashboard.
"""

import os
import sys
import requests
from datetime import datetime
from pathlib import Path

# Laad de .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    pass

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not NOTION_API_KEY or "VERVANGEN" in NOTION_API_KEY:
    print("❌ NOTION_API_KEY ontbreekt of is nog een placeholder. Vul deze in ~/recruitin/.env in.")
    sys.exit(1)

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL of SUPABASE_KEY ontbreekt. Vul deze in ~/recruitin/.env in.")
    sys.exit(1)

def fetch_latest_supabase(table: str) -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{SUPABASE_URL}/rest/v1/{table}?date=eq.{today}&select=*&limit=10"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200 and resp.json():
        return resp.json()
    return []

def sync_to_notion():
    print(f"🚀 Notion Sync naar Page ID: {NOTION_DB_ID}")

    # Haal the Supabase V2 data op van VANDAAG
    ig_data = fetch_latest_supabase("instagram_daily")
    meta_data = fetch_latest_supabase("meta_campaigns_daily")

    # Bereid the Notion API interactie voor
    notion_url = "https://api.notion.com/v1/blocks"
    notion_headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Format de data blokken
    today = datetime.now().strftime('%Y-%m-%d')

    content_blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": f"📊 Rapportage {today}"}}]}
        },
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": "📱 Instagram Metrics"}}]}
        }
    ]

    if ig_data:
        for ig in ig_data:
            hnd = ig.get('handle', 'Unknown')
            volgers = ig.get('followers', 0)
            content_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [
                    {"type": "text", "text": {"content": f"🔗 {hnd} — {volgers:,} followers"}},
                ]}
            })
    else:
        content_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "No Instagram data available"}}]}
        })

    content_blocks.append({
        "object": "block",
        "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": "💰 Meta Campaigns"}}]}
    })

    if meta_data:
        for camp in meta_data:
            name = camp.get('campaign_name', 'Unknown')
            cpl = camp.get('cpl', 0.0)
            spend = camp.get('spend', 0.0)
            leads = camp.get('leads', 0)
            status = camp.get('status', 'unknown')

            status_emoji = "🟢" if status == "green" else "🟡" if status == "yellow" else "🔴"
            content_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [
                    {"type": "text", "text": {"content": f"{status_emoji} {name}\n💵 Spend: €{spend} | 📈 Leads: {leads} | 💰 CPL: €{cpl}"}}
                ]}
            })
    else:
        content_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "No Meta campaign data available"}}]}
        })

    # Add all blocks to the page
    for block in content_blocks:
        block_payload = {
            "children": [block]
        }
        resp = requests.patch(
            f"{notion_url}/{NOTION_DB_ID}/children",
            headers=notion_headers,
            json=block_payload
        )
        if resp.status_code not in (200, 201):
            print(f"⚠️ Warning: {resp.status_code} - {resp.text}")

    print("✅ Succesvol sync naar Notion uitgevoerd!")

if __name__ == "__main__":
    sync_to_notion()
