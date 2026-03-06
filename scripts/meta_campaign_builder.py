#!/usr/bin/env python3
"""
meta_campaign_builder.py
Recruitin B.V. — TAAK 3: Meta campagne aanmaken via Marketing API v21.0

BELANGRIJK: Campagnes worden altijd als PAUSED aangemaakt.
            Wouter activeert handmatig na controle.

Gebruik:
  python3 meta_campaign_builder.py \
    --sector "oil & gas" --functie "Procesoperator" \
    --regio "Gelderland" --campagne KT_OilGas_202603 \
    --landing-url https://oil-gas.vacaturekanon.nl
"""

import os, sys, json, requests, argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Scripts pad toevoegen aan sys.path voor lokale imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "scripts"))

# Eigen Cloud Utils
from supabase_client import upload_file

# ── Config ───────────────────────────────────────────────────────────────────
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path, override=True)

BASE         = "https://graph.facebook.com/v21.0"
TOKEN        = os.getenv("META_ACCESS_TOKEN")
ACCOUNT      = os.getenv("META_ACCOUNT_ID", "act_1236576254450117")
PAGE_ID      = os.getenv("META_PAGE_ID", "660118697194302")
PIXEL        = os.getenv("META_PIXEL_ID", "238226887541404")
DAILY_BUDGET = int(os.getenv("META_DAILY_BUDGET", "1700"))   # cent, = €17
SLACK_URL    = os.getenv("SLACK_WEBHOOK_URL", "")

RETARGET_AUDIENCE = os.getenv("META_RETARGET_AUDIENCE_ID", "")
LEADS_AUDIENCE    = os.getenv("META_LEADS_AUDIENCE_ID", "")

BASE_DIR     = Path(__file__).resolve().parents[1]
default_out  = Path(os.getenv("LOCAL_OUTPUT_BASE", "/tmp/recruitin-local"))
OUTPUT_BASE  = default_out / "meta-campaigns"
ASSETS_BASE  = OUTPUT_BASE / "assets"

# ── Sector data ───────────────────────────────────────────────────────────────
SECTOR_META = {
    "oil & gas":        {"schaarste": "8.5/10", "slug": "oil-gas"},
    "constructie":      {"schaarste": "9.1/10", "slug": "constructie"},
    "automation":       {"schaarste": "9.4/10", "slug": "automation"},
    "productie":        {"schaarste": "7.8/10", "slug": "productie"},
    "renewable energy": {"schaarste": "9.7/10", "slug": "renewable-energy"},
}

# ── Hulpfuncties ─────────────────────────────────────────────────────────────

def slack(msg: str):
    if not SLACK_URL:
        print(f"[SLACK] {msg}")
        return
    try:
        requests.post(SLACK_URL, json={"text": msg}, timeout=5)
    except Exception as e:
        print(f"[SLACK ERROR] {e}")


def api(method: str, endpoint: str, data: dict = None, files=None) -> dict:
    """Wrapper voor Meta Graph API calls met error logging."""
    url = f"{BASE}/{endpoint}"
    d = {**(data or {}), "access_token": TOKEN}
    try:
        if files:
            r = requests.post(url, data=d, files=files, timeout=30)
        elif method.upper() == "GET":
            r = requests.get(url, params=d, timeout=30)
        else:
            r = requests.post(url, data=d, timeout=30)
        result = r.json()
        if "error" in result:
            print(f"   ⚠️  API error op {endpoint}: {result['error'].get('message')}")
        return result
    except Exception as e:
        print(f"   ❌ Request fout op {endpoint}: {e}")
        return {}


def sector_schaarste(sector: str) -> str:
    return SECTOR_META.get(sector.lower(), {}).get("schaarste", "8.0/10")


def build_ad_copies(sector: str, functie: str, regio: str,
                    landing_url: str, campagne_naam: str) -> list[dict]:
    """Genereert 4 ad copy varianten op basis van sector/functie/regio."""
    schaarste = sector_schaarste(sector)
    return [
        {
            "visual": "visual-1.png",
            "headline": f"Is jouw {functie} vacature al te lang open?",
            "body": (
                f"Elke maand zonder {functie} kost je direct geld.\n"
                f"Productieverlies, overwerk, gemiste opdrachten.\n"
                f"Bereken gratis jouw situatie op vacaturekanon.nl"
            ),
            "cta": "LEARN_MORE",
        },
        {
            "visual": "visual-2.png",
            "headline": f"{functie} vinden in {sector}? Score: {schaarste}",
            "body": (
                f"De {sector} arbeidsmarkt in {regio} staat onder extreme druk.\n"
                f"Weet jij hoe schaars jouw profiel echt is?\n"
                f"Gratis analyse — 10 minuten — direct in je inbox."
            ),
            "cta": "LEARN_MORE",
        },
        {
            "visual": "visual-3.png",
            "headline": f"6 weken. 3 kandidaten. {sector.title()} bedrijf, {regio}.",
            "body": (
                f"Zo snel kan het gaan als je weet waar je zoekt.\n"
                f"Gratis arbeidsmarktanalyse voor jouw {functie} vacature."
            ),
            "cta": "LEARN_MORE",
        },
        {
            "visual": "visual-4.png",
            "headline": f"Jouw concurrent werft al. Ben jij er klaar voor?",
            "body": (
                f"{sector.title()} bedrijven in {regio} kampen met recordschaarste.\n"
                f"Gratis analyse — 10 minuten — direct in je inbox."
            ),
            "cta": "LEARN_MORE",
        },
    ]


def upload_image(img_path: Path) -> str | None:
    """Upload image naar Meta Ads account. Retourneert image hash."""
    if not img_path.exists():
        print(f"   ⚠️  Image niet gevonden: {img_path} — skip upload")
        return None
    try:
        with open(img_path, "rb") as f:
            result = api("POST", f"{ACCOUNT}/adimages",
                         files={"filename": (img_path.name, f, "image/png")})
        images = result.get("images", {})
        if images:
            hash_val = list(images.values())[0].get("hash")
            print(f"   📷 Image geüpload: {img_path.name} → hash {hash_val[:12]}...")
            return hash_val
        print(f"   ⚠️  Image upload gaf geen hash: {result}")
        return None
    except Exception as e:
        print(f"   ❌ Image upload fout: {e}")
        return None


# ── Hoofd workflow ─────────────────────────────────────────────────────────────

def maak_campagne(sector: str, functie: str, regio: str,
                  landing_url: str, campagne_naam: str) -> dict:

    print(f"\n── TAAK 3: Meta Campagne ─────────────────")
    print(f"   Campagne: {campagne_naam}")
    print(f"   Sector:   {sector} | Functie: {functie} | Regio: {regio}")
    print(f"   URL:      {landing_url}")
    print(f"   Account:  {ACCOUNT}")
    print()

    if not TOKEN:
        print(f"❌ META_ACCESS_TOKEN is leeg. Pad gebruikt: {env_path} - Bestaat: {env_path.exists()}")
        print(f"Huidige process environment: META_ACCESS_TOKEN='{os.getenv('META_ACCESS_TOKEN')}'")
        sys.exit(1)

    # ── 1. Campaign aanmaken ──────────────────────────────────────────────
    print("1️⃣  Campaign aanmaken...")
    camp_result = api("POST", f"{ACCOUNT}/campaigns", {
        "name":                  campagne_naam,
        "objective":             "OUTCOME_LEADS",
        "status":                "PAUSED",
        "special_ad_categories": "[]",
    })
    campaign_id = camp_result.get("id")
    if not campaign_id:
        print(f"❌ Campaign aanmaken mislukt: {camp_result}")
        return {}
    print(f"   ✅ Campaign ID: {campaign_id}")

    # ── 2. Ad Sets aanmaken ───────────────────────────────────────────────
    print("\n2️⃣  Ad Sets aanmaken...")
    adset_configs = [
        {
            "name":    f"{campagne_naam}_Prospecting",
            "budgetpct": 60,
            "targeting": {
                "geo_locations": {
                    "countries": ["NL"],
                    "regions": [
                        {"key": "513"},   # Gelderland
                        {"key": "514"},   # Overijssel
                        {"key": "523"},   # Noord-Brabant
                        {"key": "521"},   # Noord-Holland
                        {"key": "522"},   # Zuid-Holland
                    ],
                },
                "age_min": 28,
                "age_max": 62,
                "flexible_spec": [{
                    "job_title": [
                        {"id": "103285036402772", "name": "HR Manager"},
                        {"id": "105763682788297", "name": "HR Director"},
                        {"id": "102374656463855", "name": "Chief Executive Officer"},
                        {"id": "108136692547642", "name": "Operations Manager"},
                        {"id": "132356540153",    "name": "General Manager"},
                    ],
                }],
            },
        },
        {
            "name":    f"{campagne_naam}_Lookalike",
            "budgetpct": 25,
            "targeting": {
                "geo_locations": {"countries": ["NL"]},
                "age_min": 25,
                "age_max": 65,
            },
        },
        {
            "name":    f"{campagne_naam}_Retargeting",
            "budgetpct": 15,
            "targeting": {
                "geo_locations": {"countries": ["NL"]},
                **({"custom_audiences": [{"id": RETARGET_AUDIENCE}]} if RETARGET_AUDIENCE else {}),
                **({"exclusions": {"custom_audiences": [{"id": LEADS_AUDIENCE}]}} if LEADS_AUDIENCE else {}),
            },
        },
    ]

    adset_ids = []
    daily_budget_cents = int(os.getenv("META_DAILY_BUDGET", "1700"))  # €17/dag

    for adset_cfg in adset_configs:
        budgetpct = adset_cfg.get("budgetpct", 0)
        budget = int(daily_budget_cents * budgetpct / 100)
        target = adset_cfg.get("targeting", {})
        
        if adset_cfg.get("name", "").endswith("_Retargeting") and not RETARGET_AUDIENCE:
            print(f"   ⏭️  Skip {adset_cfg.get('name')} — geen retarget audience")
            continue

        r = api("POST", f"{ACCOUNT}/adsets", {
            "name":              adset_cfg["name"],
            "campaign_id":       campaign_id,
            "daily_budget":      str(budget),
            "billing_event":     "IMPRESSIONS",
            "optimization_goal": "LEAD_GENERATION",
            "destination_type":  "WEBSITE",
            "promoted_object":   json.dumps({
                "pixel_id":          PIXEL,
                "custom_event_type": "LEAD",
            }),
            "targeting":         json.dumps(target),
            "status":            "PAUSED",
            "start_time":        datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0200"),
        })
        adset_id = r.get("id")
        if adset_id:
            adset_ids.append(adset_id)
            print(f"   ✅ {adset_cfg['name']} → {adset_id} (€{budget/100:.0f}/dag)")
        else:
            print(f"   ⚠️  Ad set mislukt: {adset_cfg['name']}")

    if not adset_ids:
        print("❌ Geen ad sets aangemaakt")
        return {"campaign_id": campaign_id}

    # ── 3. Ads aanmaken (4 varianten) ────────────────────────────────────
    print("\n3️⃣  Ads aanmaken (4 varianten)...")
    copies = build_ad_copies(sector, functie, regio, landing_url, campagne_naam)
    assets_dir = ASSETS_BASE / campagne_naam
    ad_ids = []

    for i, copy in enumerate(copies):
        print(f"\n   Ad {i+1}/{len(copies)}: {copy.get('headline', '')[:45]}...")

        # V2 eis: Fallback voor images en /tmp map voor opslag
        # Image pad constructie gebaseerd op de v2 master prompt workflow paden
        # (Als we geen images pre-genereren, pakken we de placeholder / skip errors)
        img_path = Path.home() / "recruitin-local" / "meta-campaigns" / "assets" / campagne_naam / copy.get("visual", "visual-1.png")
        if not img_path.exists():
            print(f"   ⚠️  Image niet gevonden in {img_path} — we slaan deze image nu over of gebruiken een test pad")
            # Om fouten te mocken voor de Zapier triggers: we gebruiken de "character.png" fallback indien aanwezig
            fallback_img = Path.home() / "recruitin-local" / "meta-campaigns" / "assets" / campagne_naam / "character.png"
            if fallback_img.exists():
                 img_path = fallback_img
                 print(f"   ✅ Gebruik makend van fallback image: {fallback_img}")
            
        img_hash = upload_image(img_path)

        # Creative opbouwen
        story_spec = {
            "page_id": PAGE_ID,
            "link_data": {
                "link":    landing_url,
                "message": copy["body"],
                "name":    copy["headline"],
                "call_to_action": {
                    "type":  copy["cta"],
                    "value": {"link": landing_url},
                },
            },
        }
        if img_hash:
            story_spec["link_data"]["image_hash"] = img_hash

        creative_r = api("POST", f"{ACCOUNT}/adcreatives", {
            "name":               f"{campagne_naam}_Creative_{i+1}",
            "object_story_spec":  json.dumps(story_spec),
        })
        creative_id = creative_r.get("id")
        if not creative_id:
            print(f"   ⚠️  Creative {i+1} mislukt — doorgaan...")
            continue

        # Ad aanmaken (in eerste ad set)
        prime_adset = adset_ids[0] if adset_ids else None
        if not prime_adset:
            print(f"   ⚠️  Geen adsets gevonden, ad {i+1} kan niet gecreëerd worden.")
            continue
            
        ad_r = api("POST", f"{ACCOUNT}/ads", {
            "name":     f"{campagne_naam}_Ad_{i+1}",
            "adset_id": prime_adset,
                "creative": json.dumps({"creative_id": creative_id}),
                "status":   "PAUSED",
            })
        ad_id = ad_r.get("id")
        if ad_id:
            ad_ids.append(ad_id)
            print(f"   ✅ Ad {i+1} → {ad_id}")

    # ── 4. Rapport opslaan ────────────────────────────────────────────────
    print("\n4️⃣  Resultaten opslaan...")
    rapport = {
        "campagne_naam":  campagne_naam,
        "sector":         sector,
        "functie":        functie,
        "regio":          regio,
        "landing_url":    landing_url,
        "campaign_id":    campaign_id,
        "adset_ids":      adset_ids,
        "ad_ids":         ad_ids,
        "status":         "PAUSED",
        "daily_budget":   f"€{DAILY_BUDGET/100:.2f}",
        "timestamp":      datetime.now().isoformat(),
    }

    out_dir = OUTPUT_BASE / campagne_naam
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "campaign-ids.json"
    out_file.write_text(json.dumps(rapport, indent=2, ensure_ascii=False))
    print(f"   ✅ Opgeslagen: {out_file}")

    # ── 5. Slack notificatie ──────────────────────────────────────────────
    slack(
        f"📣 {campagne_naam} — Meta campagne aangemaakt (PAUSED)\n"
        f"   Campaign ID: {campaign_id}\n"
        f"   Ad Sets: {len(adset_ids)} | Ads: {len(ad_ids)}\n"
        f"   Budget: €{DAILY_BUDGET/100:.0f}/dag\n"
        f"   Landing: {landing_url}"
    )

    print(f"\n✅ Meta campagne klaar — {campaign_id}")
    return rapport


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 6:
        print("Usage: python3 meta_campaign_builder.py <SECTOR> <FUNCTIE> <REGIO> <LANDING_URL> <CAMPAGNE_NAAM>")
        sys.exit(1)
        
    result = maak_campagne(
        sector       = sys.argv[1],
        functie      = sys.argv[2],
        regio        = sys.argv[3],
        landing_url  = sys.argv[4],
        campagne_naam= sys.argv[5],
    )
    if result.get("campaign_id"):
        print(f"\\n📋 campaign-ids.json opgeslagen")
