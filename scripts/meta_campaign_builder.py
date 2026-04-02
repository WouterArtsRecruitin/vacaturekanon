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

Of B2B Sales LeadGen:
  python3 meta_campaign_builder.py \
    --campaign-type sales-b2b \
    --campagne VK_B2B_SALES_2026 \
    --landing-url https://vacaturekanon.nl/strategie
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
PIXEL        = os.getenv("META_PIXEL_ID", "1430141541402009")
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


def build_sales_b2b_copies(landing_url: str, campagne_naam: str) -> list[dict]:
    """Genereert de specifieke B2B Sales Leadgen copies (Neon Pink & €2.495 All-In)."""
    return [
        {
            "visual": "nano_cinematic_tunnel.png",
            "headline": "Vacatures al maanden open? Tijd voor een kanon. 🚀",
            "body": (
                "De traditionele vacaturebank is dood. De beste technische vakmensen zitten al prima op hun plek bij de concurrent.\n\n"
                "Hoe bereik je ze wel? Met proactieve, algoritmische videomarketing.\n"
                "Vacaturekanon bouwt jouw AI-recruitmentmachine voor één heldere, vaste all-in prijs (€2.495,-).\n"
                "Zonder wurgcontracten of €8.000,- headhunter fees.\n\n"
                "Klik hieronder en plan direct een gratis 15-minuten strategie-sessie."
            ),
            "cta": "LEARN_MORE",
        },
        {
            "visual": "nano_dashboard_ui.png",
            "headline": "Stop met het subsidiëren van dure headhunters.",
            "body": (
                "Waarom betaal je nog 20% van een jaarsalaris om een engineer te vinden?\n\n"
                "Met Vacaturekanon bouw je voor één eenmalige investering (€2.495,-) een volautomatische AI wervingscampagne die 24/7 draait.\n"
                "Wij hanteren géén verborgen percentages en géén langlopende contracten. Jij bezit de data en de leads.\n\n"
                "Vraag vandaag nog ons rekenmodel en een korte demonstratie aan."
            ),
            "cta": "LEARN_MORE",
        },
        {
            "visual": "nano_data_bars.png",
            "headline": "Van lege werkplek naar aanname in 14 dagen.",
            "body": (
                "Elke dag dat die productiemachine leeg blijft, kost omzet.\n"
                "Vacaturekanon gaat binnen 48 uur na de intake live met hyper-gerichte AI video-advertenties die latent zoekenden over de streep trekken.\n"
                "Exclusieve leads, direct naar jou.\n\n"
                "Plan een vrijblijvende strategiesessie in via de knop."
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
                  landing_url: str, campagne_naam: str, campaign_type: str = "standaard") -> dict:

    print(f"\n── TAAK 3: Meta Campagne ─────────────────")
    print(f"   Type:     {campaign_type}")
    print(f"   Campagne: {campagne_naam}")
    if campaign_type == "standaard":
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
                "geo_locations": {"countries": ["NL"]},
                "age_min": 25,
                "age_max": 65,
                "targeting_automation": {"advantage_audience": 1},
            },
        },
        {
            "name":    f"{campagne_naam}_Lookalike",
            "budgetpct": 25,
            "targeting": {
                "geo_locations": {"countries": ["NL"]},
                "age_min": 25,
                "age_max": 65,
                "targeting_automation": {"advantage_audience": 1},
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
            "optimization_goal": "OFFSITE_CONVERSIONS",
            "bid_strategy":      "LOWEST_COST_WITHOUT_CAP",
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

    # ── 3. Ads aanmaken (variërend per type) ─────────────────────────────
    print("\n3️⃣  Ads aanmaken...")
    if campaign_type == "sales-b2b":
        copies = build_sales_b2b_copies(landing_url, campagne_naam)
    else:
        copies = build_ad_copies(sector, functie, regio, landing_url, campagne_naam)
        
    assets_dir = ASSETS_BASE / campagne_naam
    ad_ids = []

    for i, copy in enumerate(copies):
        print(f"\n   Ad {i+1}/{len(copies)}: {copy.get('headline', '')[:45]}...")

        # V2 eis: Fallback voor images en /tmp map voor opslag
        # Image pad constructie gebaseerd op de v2 master prompt workflow paden
        # (Als we geen images pre-genereren, pakken we de placeholder / skip errors)
        img_path = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/assets") / campagne_naam / copy.get("visual", "visual-1.png")
        if not img_path.exists():
            print(f"   ⚠️  Image niet gevonden in {img_path} — we slaan deze image nu over of gebruiken een test pad")
            # Om fouten te mocken voor de Zapier triggers: we gebruiken de "character.png" fallback indien aanwezig
            fallback_img = Path("/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/assets") / campagne_naam / "character.png"
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

# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recruitin B.V. Meta Campaign Builder")
    parser.add_argument("--campaign-type", default="standaard", choices=["standaard", "sales-b2b"], help="Type campagne (bepaalt ad copy en funnels)")
    parser.add_argument("--sector", default="", help="Sector (bijv 'oil & gas')")
    parser.add_argument("--functie", default="", help="Functie (bijv 'Procesoperator')")
    parser.add_argument("--regio", default="", help="Regio (bijv 'Gelderland')")
    parser.add_argument("--landing-url", required=True, help="Bestemmings URL")
    parser.add_argument("--campagne", required=True, help="Naam van de Meta campagne (bijv VK_B2B_SALES)")
    
    args = parser.parse_args()
    
    # Fallback to sys.argv positional for legacy compatibility if no flags used
    if len(sys.argv) == 6 and not any(arg.startswith("--") for arg in sys.argv):
        args.sector = sys.argv[1]
        args.functie = sys.argv[2]
        args.regio = sys.argv[3]
        args.landing_url = sys.argv[4]
        args.campagne = sys.argv[5]

    result = maak_campagne(
        sector       = args.sector,
        functie      = args.functie,
        regio        = args.regio,
        landing_url  = args.landing_url,
        campagne_naam= args.campagne,
        campaign_type= args.campaign_type
    )
    if result.get("campaign_id"):
        print(f"\n📋 campaign-ids.json opgeslagen")
