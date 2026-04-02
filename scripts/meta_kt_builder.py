#!/usr/bin/env python3
"""
meta_kt_builder.py
Kandidatentekort.nl — Meta campagne aanmaken

Genereert Image/Video ads gericht op conversies waarbij het bestand wordt geüpload op de website.
Leads komen direct in Supabase via de Vercel (worker.js) webhook.
Campagne staat standaard PAUSED voor budget monitoring en handmatige controle.
"""

import os, sys, json, requests, argparse, shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Scripts pad toevoegen aan sys.path voor lokale imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "scripts"))

# ── Config ───────────────────────────────────────────────────────────────────
env_path = BASE_DIR / "scripts" / ".kt_env"
load_dotenv(env_path, override=True)

BASE         = "https://graph.facebook.com/v21.0"
TOKEN        = os.getenv("META_ACCESS_TOKEN")
ACCOUNT      = os.getenv("META_ACCOUNT_ID", "act_1236576254450117")
PAGE_ID      = os.getenv("META_PAGE_ID", "660118697194302")
PIXEL        = os.getenv("META_PIXEL_ID", "238226887541404")
DAILY_BUDGET = int(os.getenv("META_DAILY_BUDGET", "1700"))
SLACK_URL    = os.getenv("SLACK_WEBHOOK_URL", "")

OUTPUT_BASE  = Path("/tmp/kandidatentekort_meta/meta-campaigns")
ASSETS_BASE  = OUTPUT_BASE / "assets"

def slack(msg: str):
    if not SLACK_URL: return
    try: requests.post(SLACK_URL, json={"text": msg}, timeout=5)
    except: pass

def api(method: str, endpoint: str, data: dict = None, files=None) -> dict:
    url = f"{BASE}/{endpoint}"
    d = {**(data or {}), "access_token": TOKEN}
    try:
        if files: r = requests.post(url, data=d, files=files, timeout=30)
        elif method.upper() == "GET": r = requests.get(url, params=d, timeout=30)
        else: r = requests.post(url, data=d, timeout=30)
        res = r.json()
        if "error" in res: print(f"   ⚠️ API fout ({endpoint}): {res['error'].get('message')}")
        return res
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return {}

def upload_image(img_path: Path) -> str | None:
    if not img_path.exists():
        print(f"   ⚠️ Image niet gevonden: {img_path}")
        return None
    try:
        with open(img_path, "rb") as f:
            res = api("POST", f"{ACCOUNT}/adimages", files={"filename": (img_path.name, f, "image/png")})
        images = res.get("images", {})
        if images:
            h = list(images.values())[0].get("hash")
            print(f"   📷 Uploaded {img_path.name} → hash {h[:12]}...")
            return h
        return None
    except Exception as e:
        print(f"   ❌ Image upload fout: {e}")
        return None

def build_kt_copies(sector: str, landing_url: str) -> dict:
    return {
        "headline": f"Waarom solliciteert er niemand op jouw {sector} vacature?",
        "body": (
            f"Je zoekt keihard naar technisch personeel, maar vraagt in de vacature naar een 'teamspeler zonder 9-tot-5 mentaliteit'. En het salaris is opeens 'marktconform'. Dat schrikt talent in de huidige markt direct af.\n\n"
            f"Upload de problematische vacaturetekst nu in minder dan 30 seconden op ons platform. Wij fileren de tekst en herschrijven 'm volledig op conversie.\n\n"
            f"Binnen exact 24 uur ligt er een ijzersterke, verbeterde vacaturetekst in je mailbox."
        ),
        "carousel": [
            {"image": "kt_visual_1.png", "headline": "Jij wint de prijs voor slechtste vacaturetekst"},
            {"image": "kt_visual_2.png", "headline": "Jouw huidige tekst jaagt kandidaten weg"},
            {"image": "kt_visual_3.png", "headline": "Zonder helder salaris direct geen reactie"},
            {"image": "kt_visual_4.png", "headline": "Upload de vacature in 30 sec voor herstel"},
        ]
    }

def maak_campagne(sector: str, campagne_naam: str):
    landing_url = "https://kandidatentekort.nl/#upload-sectie"
    print(f"\n── Kandidatentekort Meta Campagne ─────────────────")
    print(f"   Campagne: {campagne_naam}")
    print(f"   Sector:   {sector}")
    print(f"   URL:      {landing_url}")
    print("───────────────────────────────────────────────────")

    if not TOKEN:
        print("❌ META_ACCESS_TOKEN is leeg in .env")
        sys.exit(1)

    print("1️⃣  Campaign aanmaken...")
    camp_result = api("POST", f"{ACCOUNT}/campaigns", {
        "name": campagne_naam,
        "objective": "OUTCOME_LEADS",
        "status": "PAUSED",
        "special_ad_categories": "[]",
    })
    campaign_id = camp_result.get("id")
    if not campaign_id: return

    print("   ✅ Campaign ID:", campaign_id)

    print("\n2️⃣  Ad Set aanmaken (Prospecting)...")
    adset_r = api("POST", f"{ACCOUNT}/adsets", {
        "name": f"{campagne_naam}_Prospecting",
        "campaign_id": campaign_id,
        "daily_budget": str(DAILY_BUDGET),
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "OFFSITE_CONVERSIONS",
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "promoted_object": json.dumps({"pixel_id": PIXEL, "custom_event_type": "LEAD"}),
        "targeting": json.dumps({"geo_locations": {"countries": ["NL"]}, "age_min": 25, "age_max": 65}),
        "status": "PAUSED",
        "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0200"),
    })
    adset_id = adset_r.get("id")
    if not adset_id: return
    print("   ✅ Ad Set ID:", adset_id, f"({DAILY_BUDGET/100} euro/dag)")

    copy = build_kt_copies(sector, landing_url)
    child_attachments = []
    ad_ids = []
    assets_dir = ASSETS_BASE / campagne_naam
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n   Ad: Opbouwen Carrousel...")
    for item in copy["carousel"]:
        img_path = assets_dir / item["image"]
        img_hash = upload_image(img_path)
        if not img_hash: continue
        
        child_attachments.append({
            "link": landing_url,
            "image_hash": img_hash,
            "name": item["headline"],
            "call_to_action": {"type": "LEARN_MORE"}
        })

    if not child_attachments:
        print("   ❌ Geen images geupload. Carrousel geannuleerd.")
        return

    story_spec = {
        "page_id": PAGE_ID,
        "link_data": {
            "link": landing_url,
            "message": copy["body"],
            "child_attachments": child_attachments,
            "multi_share_end_card": False,
        }
    }

    creative_r = api("POST", f"{ACCOUNT}/adcreatives", {
        "name": f"{campagne_naam}_Creative_Carousel",
        "object_story_spec": json.dumps(story_spec),
    })
    creative_id = creative_r.get("id")
    
    if creative_id:
        ad_r = api("POST", f"{ACCOUNT}/ads", {
            "name": f"{campagne_naam}_Ad_Carousel",
            "adset_id": adset_id,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": "PAUSED",
        })
        if "id" in ad_r:
            ad_ids.append(ad_r["id"])
            print("   ✅ Carousel Ad succesvol aangemaakt:", ad_r["id"])

    # 4. Resultaat opslaan
    out_file = OUTPUT_BASE / campagne_naam / "rapport.json"
    (OUTPUT_BASE / campagne_naam).mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({
        "status": "PAUSED", "campaign_id": campaign_id, "ads": ad_ids
    }, indent=2))

    slack(f"🎯 Meta campagne: {campagne_naam}\nStatus: PAUSED\nBudget: €{DAILY_BUDGET/100}/d\nAds gecreëerd: {len(ad_ids)}")
    print("\n✅ Klaar! Resultaten weggeschreven.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", required=True)
    parser.add_argument("--campagne", required=True)
    args = parser.parse_args()
    maak_campagne(args.sector, args.campagne)
