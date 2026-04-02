#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   META CAMPAIGN OPTIMIZER & ANALYTICS                                    ║
║   Recruitin B.V. | Vacaturekanon                                         ║
║                                                                          ║
║   Doel:                                                                  ║
║   - Haalt dagelijks metrics (CPL, CTR, Spend) op uit Meta Graph API      ║
║   - Stuurt campagnes automatisch bij (pauzeer slecht presenterende ads)  ║
║   - Logt alles in Supabase (vk_metrics)                                  ║
║   - Stuurt een Slack notificatie met een samenvatting                    ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# --- CONFIGURATIE ---
# In een productieomgeving worden deze uit .env of keychain gehaald.
from dotenv import load_dotenv
load_dotenv("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/.env", override=True)

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("META_ACCOUNT_ID", "act_1236576254450117")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# --- KPI GRENZEN (AUTOPILOT LOGICA) ---
MAX_CPL_THRESHOLD = 35.00       # Meer dan €35 per lead = kritiek
MIN_CTR_THRESHOLD = 0.6         # Lager dan 0.6% CTR = slechte hook/creative
MAX_SPEND_ZERO_LEADS = 25.00    # €25 gespendeerd maar 0 leads = pauzeren

def fetch_campaign_metrics():
    """Haal metrics op voor alle actieve campagnes via Meta Graph API (laatste 7 dagen)"""
    print("📊 Start Meta Analytics Fetch...")

    if not META_ACCESS_TOKEN:
        print("   ❌ META_ACCESS_TOKEN niet gevonden — kan geen metrics ophalen.")
        return []

    url = f"https://graph.facebook.com/v21.0/{AD_ACCOUNT_ID}/insights"
    params = {
        "level": "ad",
        "fields": "ad_id,ad_name,campaign_name,spend,impressions,clicks,actions",
        "date_preset": "last_7d",
        "limit": 100,
        "access_token": META_ACCESS_TOKEN
    }

    try:
        req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}")
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"   ❌ Meta API fout: {e}")
        return []

    metrics = []
    for row in data.get("data", []):
        leads = 0
        for action in row.get("actions", []):
            if action.get("action_type") == "lead":
                leads = int(action.get("value", 0))
        metrics.append({
            "ad_id": row.get("ad_id", ""),
            "ad_name": row.get("ad_name", ""),
            "campaign_name": row.get("campaign_name", ""),
            "spend": float(row.get("spend", 0)),
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "leads": leads
        })

    print(f"   📈 {len(metrics)} ad rows opgehaald uit Meta API")
    return metrics


def pause_meta_ad(ad_id: str):
    """Pauzeer een specifieke advertentie in Meta via de Graph API"""
    if not META_ACCESS_TOKEN:
        print(f"   ⚠️ Kan ad {ad_id} niet pauzeren — geen token")
        return

    url = f"https://graph.facebook.com/v21.0/{ad_id}"
    payload = json.dumps({"status": "PAUSED", "access_token": META_ACCESS_TOKEN}).encode()
    req = urllib.request.Request(url, data=payload, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
        print(f"   🔻 Ad {ad_id} gepauzeerd via Meta API")
    except Exception as e:
        print(f"   ❌ Pauzeren ad {ad_id} mislukt: {e}")

def save_to_supabase(metrics: list):
    """Sla de berekende metrics op in Supabase voor Looker Studio / Dashboards"""
    print("  💾 Opslaan in Supabase (vk_metrics)...")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("     [!] Supabase credentials missen, skip opslaan.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    for row in metrics:
        payload = {
            "date": today,
            "campaign": row["campaign_name"],
            "ad_name": row["ad_name"],
            "spend": row["spend"],
            "impressions": row["impressions"],
            "cpc": row["cpc"],
            "cpl": row["cpl"],
            "ctr": row["ctr"]
        }
        req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/vk_metrics", data=json.dumps(payload).encode(), method="POST",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"     [!] Fout bij opslaan: {e}")

def notify_slack(report_text: str):
    """Stuur het analyserapport naar Slack"""
    payload = {
        "channel": "#leads-meta",
        "text": report_text
    }
    req = urllib.request.Request(SLACK_WEBHOOK_URL, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Slack webhook failed: {e}")

def analyze_and_steer():
    """Core logica om data te pakken, analyseren en handelen."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔥 AUTO-OPTIMIZER GEBOUWD DOOR ANTIGRAVITY 🔥\n")

    raw_data = fetch_campaign_metrics()
    processed_metrics = []
    
    slack_lines = ["📈 *DAGELIJKSE META ADS ANALYSE & OPTIMALISATIE* 📈\n"]
    actions_taken = 0

    for ad in raw_data:
        # 1. BEREKEN METRICS
        spend = float(ad.get('spend', 0))
        clicks = int(ad.get('clicks', 0))
        impressions = int(ad.get('impressions', 0))
        leads = int(ad.get('leads', 0))

        ctr = float((clicks / impressions * 100) if impressions > 0 else 0)
        cpc = float((spend / clicks) if clicks > 0 else 0)
        cpl = float((spend / leads) if leads > 0 else spend)  # Als 0 leads, is theoretisch CPL gelijk aan spend of hoger

        processed_metrics.append({
            "campaign_name": ad["campaign_name"],
            "ad_name": ad['ad_name'],
            "spend": spend, "impressions": impressions, "ctr": ctr, "cpc": cpc, "cpl": cpl
        })

        insight = f"• {ad['ad_name']}: Spend €{spend:.2f} | CTR: {ctr:.2f}% | Leads: {leads} (CPL: €{cpl:.2f})"
        print(insight)
        
        # 2. AUTOPILOT REGELS
        action_msg = ""
        
        # Scenario A: Bloedende ad (Hoge spend, 0 leads, lage CTR)
        if leads == 0 and spend > MAX_SPEND_ZERO_LEADS:
            action_msg = "❌ AUTOPAUSE: Weggegooid geld. 0 Leads bij max spend."
            pause_meta_ad(ad['ad_id'])
            actions_taken += 1
            
        # Scenario B: Dure leads (CPL hoger dan acceptabel)
        elif leads > 0 and cpl > MAX_CPL_THRESHOLD:
            action_msg = f"⚠️ WAARSCHUWING: Leads zijn te duur (>{MAX_CPL_THRESHOLD}!). Ad afgeschaald."
            pause_meta_ad(ad['ad_id'])
            actions_taken += 1
            
        # Scenario C: Slechte CTR (Hook in video / Image sucks)
        elif impressions > 1000 and ctr < MIN_CTR_THRESHOLD:
            action_msg = "⚠️ WAARSCHUWING: Niemand klikt door (Slechte CTR). Overweeg nieuwe video generatie."
        
        if action_msg:
            slack_lines.append(f"{insight}\n  👉 _{action_msg}_")
        else:
            slack_lines.append(f"{insight} (✅ Gezond)")

    # 3. VERWERK RESULTATEN
    save_to_supabase(processed_metrics)

    if actions_taken > 0:
        slack_lines.insert(1, f"⚠️ *Let op:* De Autopilot heeft zojuist {actions_taken} advertenties gepauzeerd.\n")
    else:
        slack_lines.insert(1, "✅ Alle lopende ads presteren momenteel binnen de grenzen.\n")
        
    final_report = "\n".join(slack_lines)
    notify_slack(final_report)
    print("\n✅ Analyse voltooid. Slack genotificeerd.")

if __name__ == "__main__":
    analyze_and_steer()
