#!/usr/bin/env python3
"""
Agent 04 — Meta Marketing API Campaign Creator
Upload visuals, genereer ad copy via Claude, maak campagne aan (altijd PAUSED).
Output: ad-copy.json, image-hashes.json, campaign-report.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import requests

BASE_DIR = Path(__file__).parent.parent
CAMPAIGNS_DIR = BASE_DIR / "campaigns"

AD_TYPES = ["schaarste", "kosten", "social_proof", "urgentie"]
AD_SET_SPLITS = {
    "prospecting":  0.60,
    "lookalike":    0.25,
    "retargeting":  0.15,
}

# Meta API
META_API_BASE = "https://graph.facebook.com/v20.0"


def get_env(key: str) -> str:
    val = os.environ.get(key, "")
    if not val:
        print(f"[FOUT] Env var niet gevonden: {key}")
        print(f"Controleer ~/.zshrc of keychain setup.")
        sys.exit(1)
    return val


def meta_post(endpoint: str, token: str, data: dict, files=None) -> dict:
    url = f"{META_API_BASE}/{endpoint}"
    params = {"access_token": token}
    if files:
        resp = requests.post(url, params=params, data=data, files=files, timeout=30)
    else:
        resp = requests.post(url, params=params, json=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def meta_get(endpoint: str, token: str, params: dict = None) -> dict:
    url = f"{META_API_BASE}/{endpoint}"
    p = {"access_token": token}
    if params:
        p.update(params)
    resp = requests.get(url, params=p, timeout=30)
    resp.raise_for_status()
    return resp.json()


def upload_image(image_path: Path, account_id: str, token: str) -> str:
    """Upload PNG naar Meta, return image_hash."""
    print(f"  Upload: {image_path.name}...")
    with open(image_path, "rb") as f:
        result = meta_post(
            f"act_{account_id}/adimages",
            token,
            data={"filename": image_path.name},
            files={"filename": (image_path.name, f, "image/png")},
        )
    images = result.get("images", {})
    for fname, info in images.items():
        return info["hash"]
    raise ValueError(f"Geen hash teruggekomen voor {image_path.name}")


def generate_ad_copy(client: anthropic.Anthropic, input_data: dict, ad_type: str) -> dict:
    """Genereer ad copy via Claude Sonnet."""

    type_instructies = {
        "schaarste": "Focus op schaarste en exclusiviteit. Benadruk dat er maar een beperkt aantal plekken is.",
        "kosten":    "Focus op het salaris, arbeidsvoorwaarden en financieel voordeel.",
        "social_proof": "Focus op sociaal bewijs: hoeveel mensen zijn al geplaatst, wat zeggen anderen.",
        "urgentie":  "Focus op tijdsdruk en urgentie. De vacature sluit binnenkort.",
    }

    functie = input_data["functie"]
    sector = input_data["sector"]
    regio = ", ".join(input_data["regio"])
    salaris = input_data["salaris_range"]
    pijn = input_data["pijn_punt"]
    usps = input_data["usps"]

    prompt = f"""Schrijf Meta Ads copy voor een recruitment advertentie. Geef JSON terug.

Doelgroep: {functie} in {sector}, regio {regio}
Salaris: {salaris} bruto/jaar
Pijnpunt doelgroep: {pijn}
USPs: {'; '.join(usps)}
Ad type instructie: {type_instructies[ad_type]}

Schrijf 3 varianten voor elk veld. Geef compact, directe tekst voor mobiel.

Geef ALLEEN geldige JSON terug:
{{
  "primary_text": ["variant1", "variant2", "variant3"],
  "headline": ["variant1", "variant2", "variant3"],
  "description": ["variant1", "variant2", "variant3"],
  "cta": "APPLY_NOW"
}}

Regels:
- primary_text: max 125 tekens
- headline: max 40 tekens, pakkend
- description: max 30 tekens
- Geen emojis in headline
- Spreek direct aan ("Jij" / "Jouw")
- Nederlands"""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()

    # Extract JSON
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def create_campaign(account_id: str, token: str, campagne: str, dry_run: bool) -> str:
    if dry_run:
        fake_id = f"DRYRUN_{campagne[:8]}_{int(time.time())}"
        print(f"  [DRY-RUN] Campagne ID: {fake_id}")
        return fake_id

    data = {
        "name": campagne,
        "objective": "OUTCOME_LEADS",
        "status": "PAUSED",
        "special_ad_categories": [],
    }
    result = meta_post(f"act_{account_id}/campaigns", token, data)
    campaign_id = result["id"]
    print(f"  Campagne aangemaakt: {campaign_id}")
    return campaign_id


def create_ad_set(
    account_id: str, token: str, campaign_id: str,
    name: str, ad_set_type: str,
    daily_budget_cents: int, pixel_id: str,
    targeting: dict, dry_run: bool
) -> str:
    if dry_run:
        fake_id = f"DRYRUN_ADSET_{ad_set_type}_{int(time.time())}"
        print(f"  [DRY-RUN] Ad Set '{name}': {fake_id}")
        return fake_id

    data = {
        "name": name,
        "campaign_id": campaign_id,
        "daily_budget": daily_budget_cents,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "LEAD_GENERATION",
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "status": "PAUSED",
        "targeting": targeting,
        "promoted_object": {"pixel_id": pixel_id, "custom_event_type": "LEAD"},
    }
    result = meta_post(f"act_{account_id}/adsets", token, data)
    ad_set_id = result["id"]
    print(f"  Ad Set '{name}': {ad_set_id}")
    return ad_set_id


def build_targeting(ad_set_type: str, regio: list, input_data: dict) -> dict:
    """Bouw targeting object per ad set type."""
    nl_geo = {
        "Gelderland": {"key": "aDxjiZAbub"},
        "Overijssel": {"key": "aDxjiZAbuc"},
        "Noord-Brabant": {"key": "aDxjiZAbud"},
    }
    geo_locations = {
        "regions": [{"key": nl_geo.get(r, {}).get("key", r)} for r in regio],
        "location_types": ["home", "recent"],
    }

    base = {
        "geo_locations": geo_locations,
        "age_min": 25,
        "age_max": 55,
        "locales": [24],  # Nederlands
    }

    if ad_set_type == "prospecting":
        base["flexible_spec"] = [
            {"interests": [
                {"id": "6003139266461", "name": "Engineering"},
                {"id": "6003397425735", "name": "Manufacturing"},
            ]}
        ]
    elif ad_set_type == "lookalike":
        # Lookalike audience — vereist custom audience ID in productie
        base["custom_audiences"] = [{"id": "LOOKALIKE_AUDIENCE_ID"}]
    elif ad_set_type == "retargeting":
        base["custom_audiences"] = [{"id": "PIXEL_RETARGET_AUDIENCE_ID"}]
        base["age_min"] = 22
        base["age_max"] = 60

    return base


def create_ad(
    account_id: str, token: str, ad_set_id: str,
    creative_id: str, name: str, dry_run: bool
) -> str:
    if dry_run:
        fake_id = f"DRYRUN_AD_{name[:8]}_{int(time.time())}"
        print(f"    [DRY-RUN] Ad '{name}': {fake_id}")
        return fake_id

    data = {
        "name": name,
        "adset_id": ad_set_id,
        "creative": {"creative_id": creative_id},
        "status": "PAUSED",
    }
    result = meta_post(f"act_{account_id}/ads", token, data)
    ad_id = result["id"]
    print(f"    Ad '{name}': {ad_id}")
    return ad_id


def create_creative(
    account_id: str, token: str, page_id: str,
    name: str, image_hash: str, copy_data: dict,
    jotform_url: str, dry_run: bool
) -> str:
    if dry_run:
        fake_id = f"DRYRUN_CREATIVE_{name[:8]}_{int(time.time())}"
        print(f"    [DRY-RUN] Creative '{name}': {fake_id}")
        return fake_id

    data = {
        "name": name,
        "object_story_spec": {
            "page_id": page_id,
            "link_data": {
                "image_hash": image_hash,
                "link": jotform_url,
                "message": copy_data["primary_text"][0],
                "name": copy_data["headline"][0],
                "description": copy_data["description"][0],
                "call_to_action": {"type": copy_data.get("cta", "APPLY_NOW")},
            }
        },
    }
    result = meta_post(f"act_{account_id}/adcreatives", token, data)
    creative_id = result["id"]
    print(f"    Creative '{name}': {creative_id}")
    return creative_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campagne", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-visuals", action="store_true", help="Sla visual upload over")
    args = parser.parse_args()

    campagne = args.campagne
    campagne_dir = CAMPAIGNS_DIR / campagne.replace(" ", "_")

    # Laad config
    config_file = campagne_dir / "campaign-input.json"
    if not config_file.exists():
        print(f"[FOUT] campaign-input.json niet gevonden. Voer eerst Agent 03 uit.")
        sys.exit(1)
    input_data = json.loads(config_file.read_text())

    print(f"\n=== Agent 04: Meta Campaign Creator ===")
    print(f"Campagne: {campagne}")
    if args.dry_run:
        print("[DRY-RUN modus — geen echte API calls]\n")

    # Env vars
    token = get_env("META_ACCESS_TOKEN")
    account_id = get_env("META_ACCOUNT_ID").lstrip("act_")
    pixel_id = get_env("META_PIXEL_ID")
    jotform_id = get_env("JOTFORM_FORM_ID")
    anthropic_key = get_env("ANTHROPIC_API_KEY")
    jotform_url = os.environ.get("JOTFORM_URL") or f"https://eu.jotform.com/{jotform_id}"

    # Meta Page ID ophalen
    if not args.dry_run:
        pages = meta_get("me/accounts", token)
        page_id = pages["data"][0]["id"] if pages.get("data") else None
        if not page_id:
            print("[FOUT] Geen Facebook Page gevonden op dit account.")
            sys.exit(1)
        print(f"Facebook Page ID: {page_id}")
    else:
        page_id = "DRYRUN_PAGE_ID"

    # 1. Upload visuals
    image_hashes = {}
    if not args.skip_visuals:
        print("\n[1] Visuals uploaden...")
        assets_dir = campagne_dir / "assets"
        for ad_type in AD_TYPES:
            candidates = [
                assets_dir / f"{ad_type}.png",
                campagne_dir / f"{ad_type}.png",
                BASE_DIR / "assets" / f"{ad_type}.png",
            ]
            img_path = next((p for p in candidates if p.exists()), None)
            if not img_path:
                print(f"  [SKIP] Visual niet gevonden: {ad_type}.png")
                image_hashes[ad_type] = f"MISSING_{ad_type}"
                continue

            if args.dry_run:
                image_hashes[ad_type] = f"DRYRUN_HASH_{ad_type}"
                print(f"  [DRY-RUN] {ad_type}: DRYRUN_HASH_{ad_type}")
            else:
                image_hashes[ad_type] = upload_image(img_path, account_id, token)

        hashes_file = campagne_dir / "image-hashes.json"
        hashes_file.write_text(json.dumps(image_hashes, indent=2))
        print(f"Hashes opgeslagen: {hashes_file}")
    else:
        hashes_file = campagne_dir / "image-hashes.json"
        if hashes_file.exists():
            image_hashes = json.loads(hashes_file.read_text())
            print(f"[SKIP] Bestaande hashes geladen: {hashes_file}")

    # 2. Ad copy genereren via Claude
    print("\n[2] Ad copy genereren via Claude...")
    client = anthropic.Anthropic(api_key=anthropic_key)
    all_copy = {}
    for ad_type in AD_TYPES:
        print(f"  Genereer: {ad_type}...")
        copy = generate_ad_copy(client, input_data, ad_type)
        all_copy[ad_type] = copy

    copy_file = campagne_dir / "ad-copy.json"
    copy_file.write_text(json.dumps(all_copy, indent=2, ensure_ascii=False))
    print(f"Ad copy opgeslagen: {copy_file}")

    # 3. Campagne aanmaken
    print(f"\n[3] Campagne aanmaken...")
    campaign_id = create_campaign(account_id, token, campagne, args.dry_run)

    # 4. Ad sets aanmaken
    print(f"\n[4] Ad sets aanmaken (3 sets)...")
    daily_budget_cents = int(input_data["dagbudget"] * 100)
    ad_set_ids = {}

    for ad_set_type, pct in AD_SET_SPLITS.items():
        name = f"{campagne} — {ad_set_type.capitalize()}"
        budget_cents = int(daily_budget_cents * pct)
        targeting = build_targeting(ad_set_type, input_data["regio"], input_data)
        ad_set_id = create_ad_set(
            account_id, token, campaign_id, name, ad_set_type,
            budget_cents, pixel_id, targeting, args.dry_run
        )
        ad_set_ids[ad_set_type] = ad_set_id

    # 5. Creatives + Ads aanmaken (4 per ad set)
    print(f"\n[5] Creatives en ads aanmaken (4x per ad set)...")
    all_ad_ids = {}

    for ad_set_type, ad_set_id in ad_set_ids.items():
        print(f"\n  Ad set: {ad_set_type}")
        all_ad_ids[ad_set_type] = []

        for ad_type in AD_TYPES:
            copy_data = all_copy[ad_type]
            image_hash = image_hashes.get(ad_type, "MISSING")
            creative_name = f"{campagne} | {ad_type}"

            creative_id = create_creative(
                account_id, token, page_id,
                creative_name, image_hash, copy_data,
                jotform_url, args.dry_run
            )

            ad_name = f"{campagne} | {ad_set_type} | {ad_type}"
            ad_id = create_ad(account_id, token, ad_set_id, creative_id, ad_name, args.dry_run)
            all_ad_ids[ad_set_type].append({
                "ad_type": ad_type,
                "ad_id": ad_id,
                "creative_id": creative_id,
            })

    # 6. Rapport
    report = {
        "campagne": campagne,
        "aangemaakt": datetime.now().isoformat(),
        "dry_run": args.dry_run,
        "campaign_id": campaign_id,
        "status": "PAUSED",
        "page_id": page_id,
        "account_id": account_id,
        "pixel_id": pixel_id,
        "jotform_url": jotform_url,
        "dagbudget": input_data["dagbudget"],
        "cpl_max": input_data["cpl_max"],
        "cpl_goed": input_data["cpl_goed"],
        "ctr_min": input_data["ctr_min"],
        "ad_sets": ad_set_ids,
        "ads": all_ad_ids,
        "image_hashes": image_hashes,
    }
    report_file = campagne_dir / "campaign-report.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n=== Campagne aangemaakt (PAUSED) ===")
    print(f"Campaign ID: {campaign_id}")
    print(f"Ad sets:     {len(ad_set_ids)}")
    print(f"Ads totaal:  {sum(len(v) for v in all_ad_ids.values())}")
    print(f"Rapport:     {report_file}")
    print(f"\nACTIE: Ga naar Meta Ads Manager om de campagne te reviewen en handmatig te activeren.")
    print(f"\nAgent 04 klaar.")


if __name__ == "__main__":
    main()
