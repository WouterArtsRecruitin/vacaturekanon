#!/usr/bin/env python3
"""
jotform_to_landing.py — Jotform data → landing page generator
Recruitin B.V.

Exacte veldnamen van form 252881347421054:
  q2_textbox0  → Functietitel
  q3_textbox1  → Locatie/Regio
  q6_textarea4 → Vacaturetekst
  q7_textbox5  → Vacature URL
  emailfor     → E-mail voor Rapportage

Gebruik:
  python3 jotform_to_landing.py --submission-id 123456789
  python3 jotform_to_landing.py --json-file test_data.json
  python3 jotform_to_landing.py  (demo data)
  python3 jotform_to_landing.py --report  (toon mapping rapport)
"""

import json, os, re, sys, argparse, requests, time
from pathlib import Path
from datetime import datetime

# .env laden
env_path = Path(__file__).resolve().parents[1] / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(env_path, override=True)
except ImportError:
    pass

# ─── JOTFORM VELD MAPPING ─────────────────────────────────────────────────────
FIELD_MAPPING = {
    # Exacte veldnamen van jouw form
    "q2_textbox0":       "{{FUNCTIE}}",
    "q3_textbox1":       "{{REGIO}}",
    "q6_textarea4":      "{{VACATURETEKST}}",
    "q7_textbox5":       "{{VACATURE_URL}}",
    "emailfor":          "{{CONTACT_EMAIL}}",

    # Aliassen
    "functietitel":      "{{FUNCTIE}}",
    "functie":           "{{FUNCTIE}}",
    "locatie":           "{{REGIO}}",
    "regio":             "{{REGIO}}",
    "vacaturetekst":     "{{VACATURETEKST}}",
    "omschrijving":      "{{VACATURETEKST}}",
    "vacature_url":      "{{VACATURE_URL}}",
    "contact_email":     "{{CONTACT_EMAIL}}",

    # Uitbreidbaar voor toekomstige forms
    "bedrijf":           "{{BEDRIJF}}",
    "bedrijfsnaam":      "{{BEDRIJF}}",
    "sector":            "{{SECTOR}}",
    "salaris":           "{{SALARIS}}",
    "salaris_min":       "{{SALARIS_MIN}}",
    "salaris_max":       "{{SALARIS_MAX}}",
    "vereisten":         "{{VEREISTEN_LIJST}}",
    "voordelen":         "{{VOORDELEN_LIJST}}",
    "website":           "{{BEDRIJF_URL}}",
    "campagne_naam":     "{{CAMPAGNE}}",
    "cta_url":           "{{CTA_URL}}",
}

# ─── SECTOR DESIGN MAPPING ───────────────────────────────────────────────────
# Sector → (brand_primary, brand_secondary, hero_image_url)
SECTOR_DESIGN = {
    "constructie": (
        "#1a3a5c", "#2563eb",
        "https://images.unsplash.com/photo-1504307651254-35680f356dfd?q=80&w=2670&auto=format&fit=crop"
    ),
    "productie": (
        "#1c3a2a", "#16a34a",
        "https://images.unsplash.com/photo-1565043666747-69f6646db940?q=80&w=2670&auto=format&fit=crop"
    ),
    "automation": (
        "#1e1b4b", "#7c3aed",
        "https://images.unsplash.com/photo-1581091226033-d5c48150dbaa?q=80&w=2670&auto=format&fit=crop"
    ),
    "oil-gas": (
        "#2d1b0e", "#c2410c",
        "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2670&auto=format&fit=crop"
    ),
    "renewable-energy": (
        "#0c2a1a", "#059669",
        "https://images.unsplash.com/photo-1466611653911-95081537e5b7?q=80&w=2670&auto=format&fit=crop"
    ),
    "finance": (
        "#1a1a2e", "#1e3a8a",
        "https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=2670&auto=format&fit=crop"
    ),
    "logistiek": (
        "#1a2744", "#1d4ed8",
        "https://images.unsplash.com/photo-1586528116375-c4dcccc76b73?q=80&w=2670&auto=format&fit=crop"
    ),
    "default": (
        "#0f2027", "#203a43",
        "https://images.unsplash.com/photo-1521791136064-7986c2920216?q=80&w=2670&auto=format&fit=crop"
    ),
}

# Functietitel keywords → sector mapping
FUNCTIE_SECTOR_MAP = {
    "planner": "logistiek", "supply chain": "logistiek", "logistiek": "logistiek",
    "transport": "logistiek", "warehouse": "logistiek", "magazijn": "logistiek",
    "plc": "automation", "scada": "automation", "robot": "automation",
    "automatisering": "automation", "mechatronica": "automation", "software": "automation",
    "engineer": "automation", "it": "automation", "developer": "automation",
    "bouw": "constructie", "uitvoerder": "constructie", "calculator": "constructie",
    "projectleider": "constructie", "werkvoorbereider": "constructie",
    "operator": "oil-gas", "raffinaderij": "oil-gas", "petrochemie": "oil-gas",
    "solar": "renewable-energy", "wind": "renewable-energy", "energie": "renewable-energy",
    "productie": "productie", "teamlead": "productie", "kwaliteit": "productie",
    "manufacturing": "productie", "proces": "productie", "technisch": "productie",
    "accounting": "finance", "finance": "finance", "controller": "finance",
    "financieel": "finance", "administratie": "finance",
}

def detect_sector(functie: str) -> str:
    """Detecteer sector op basis van functietitel keywords."""
    functie_lower = functie.lower()
    for keyword, sector in FUNCTIE_SECTOR_MAP.items():
        if keyword in functie_lower:
            return sector
    return "default"

DEFAULTS = {
    "{{FUNCTIE}}":           "Technisch Specialist",
    "{{REGIO}}":             "Nederland",
    "{{SECTOR}}":            "Techniek",
    "{{BEDRIJF}}":           "Ons bedrijf",
    "{{SALARIS}}":           "Marktconform salaris",
    "{{SALARIS_MIN}}":       "3.500",
    "{{SALARIS_MAX}}":       "5.500",
    "{{CONTRACT_TYPE}}":     "Vaste dienst",
    "{{UREN_PER_WEEK}}":     "40",
    "{{OPLEIDINGSNIVEAU}}":  "MBO/HBO",
    "{{ERVARING_JAREN}}":    "2+",
    "{{CONTACT_EMAIL}}":     "info@recruitin.nl",
    "{{CAMPAGNE}}":          f"campagne_{datetime.now().strftime('%Y%m%d')}",
    "{{CTA_URL}}":           "https://kandidatentekort.nl",
    "{{HERO_IMAGE}}":        SECTOR_DESIGN["default"][2],
    "{{META_PIXEL_ID}}":     os.getenv("META_PIXEL_ID", ""),
    "{{PROFIEL_OMSCHRIJVING}}": "Je hebt relevante werkervaring en bent klaar voor een nieuwe uitdaging.",
    "{{VACATURETEKST}}":     "Een mooie kans voor een gedreven professional.",
    "{{SALARIS_OMSCHRIJVING}}": "Een marktconform salaris passend bij jouw ervaring en opleiding.",
    "{{VEREISTEN_LIJST}}":   "<li>Relevante werkervaring</li><li>Proactieve houding</li><li>Teamspeler</li>",
    "{{VOORDELEN_LIJST}}":   "<li>Marktconform salaris</li><li>Goede secundaire arbeidsvoorwaarden</li><li>Ruimte voor groei</li>",
}


def fetch_jotform_submission(submission_id: str) -> dict:
    api_key = os.getenv("JOTFORM_API_KEY")
    if not api_key:
        print("⚠️ JOTFORM_API_KEY niet ingesteld")
        return {}
    url = f"https://eu-api.jotform.com/submission/{submission_id}"
    resp = requests.get(url, params={"apiKey": api_key}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("responseCode") != 200:
        raise ValueError(f"Jotform API error: {data}")
    answers = data["content"]["answers"]
    result = {}
    for qid, answer in answers.items():
        naam = answer.get("name", "").lower().strip()
        waarde = answer.get("answer", "")
        if naam and waarde:
            result[naam] = str(waarde) if not isinstance(waarde, list) else ", ".join(waarde)
    print(f"✅ Jotform submission geladen: {len(result)} velden")
    return result


def map_to_template_vars(jotform_data: dict) -> dict:
    template_vars = dict(DEFAULTS)
    for field_name, value in jotform_data.items():
        field_lower = field_name.lower().strip()
        if field_lower in FIELD_MAPPING:
            tag = FIELD_MAPPING[field_lower]
            template_vars[tag] = value
        else:
            for mapping_key, tag in FIELD_MAPPING.items():
                if mapping_key in field_lower or field_lower in mapping_key:
                    if tag not in template_vars or template_vars[tag] == DEFAULTS.get(tag, ""):
                        template_vars[tag] = value
                    break

    # Vacaturetekst → profiel omschrijving + salaris
    if template_vars.get("{{VACATURETEKST}}") != DEFAULTS["{{VACATURETEKST}}"]:
        vacaturetekst = template_vars["{{VACATURETEKST}}"]
        # Eerste 2 zinnen → profiel omschrijving
        zinnen = [z.strip() for z in re.split(r'[.!?]\s+', vacaturetekst) if z.strip()]
        if len(zinnen) >= 2:
            template_vars["{{PROFIEL_OMSCHRIJVING}}"] = ". ".join(zinnen[:2]) + "."
        elif zinnen:
            template_vars["{{PROFIEL_OMSCHRIJVING}}"] = zinnen[0]
        # Vereisten extraheren (regels met -, •, *, of nummers)
        vereisten_regels = re.findall(r'^[-•*\d\.]\s*(.+)$', vacaturetekst, re.MULTILINE)
        if vereisten_regels:
            template_vars["{{VEREISTEN_LIJST}}"] = "\n".join(
                f"<li>{r.strip()}</li>" for r in vereisten_regels[:6]
            )

    # Salaris range
    if template_vars["{{SALARIS_MIN}}"] != DEFAULTS["{{SALARIS_MIN}}"]:
        template_vars["{{SALARIS_OMSCHRIJVING}}"] = (
            f"Een salaris tussen €{template_vars['{{SALARIS_MIN}}']} en "
            f"€{template_vars['{{SALARIS_MAX}}']} per maand, "
            f"afhankelijk van jouw ervaring en opleiding."
        )

    return template_vars


def get_branding(bedrijf_url: str, bedrijf_naam: str) -> dict:
    branding = {
        "__BRAND_PRIMARY__":   "#E8630A",
        "__BRAND_SECONDARY__": "#D35400",
        "{{KLANT_LOGO_HTML}}": f'<span class="logo">{bedrijf_naam}</span>',
    }
    if not bedrijf_url:
        return branding
    try:
        if not bedrijf_url.startswith("http"):
            bedrijf_url = "https://" + bedrijf_url
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(bedrijf_url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if any(k in (src + img.get("alt", "") + " ".join(img.get("class", []))).lower()
                   for k in ["logo", "brand"]):
                logo_url = urljoin(bedrijf_url, src)
                branding["{{KLANT_LOGO_HTML}}"] = f'<img src="{logo_url}" alt="{bedrijf_naam}" class="logo">'
                break
        meta_color = soup.find("meta", attrs={"name": "theme-color"})
        if meta_color and meta_color.get("content"):
            c = meta_color["content"]
            branding["__BRAND_PRIMARY__"] = c
            branding["__BRAND_SECONDARY__"] = c
    except Exception as e:
        print(f"⚠️ Branding scrapen mislukt: {e}")
    return branding


# ── POST-GENERATIE INTEGRATIES ────────────────────────────────────────────

def deploy_to_netlify(output_dir: Path, campagne: str, sector: str) -> str | None:
    """Deploy landingspagina naar Netlify. Geeft live URL terug."""
    netlify_token = os.getenv("NETLIFY_TOKEN")
    if not netlify_token:
        print("   ⚠️  NETLIFY_TOKEN niet ingesteld — deploy skip")
        return None

    # Kies site ID op basis van sector
    sector_site_map = {
        "oil-gas":        os.getenv("NETLIFY_SITE_OIL_GAS"),
        "constructie":    os.getenv("NETLIFY_SITE_CONSTRUCTIE"),
        "automation":     os.getenv("NETLIFY_SITE_AUTOMATION"),
        "productie":      os.getenv("NETLIFY_SITE_PRODUCTIE"),
        "renewable-energy": os.getenv("NETLIFY_SITE_PRODUCTIE"),
    }
    site_id = sector_site_map.get(sector) or os.getenv("NETLIFY_SITE_CONSTRUCTIE")
    if not site_id:
        print("   ⚠️  Geen Netlify site ID voor sector — deploy skip")
        return None

    print(f"   🚀 Netlify deploy: {campagne} → {site_id[:8]}...")
    try:
        result = subprocess.run(
            ["npx", "netlify-cli", "deploy", "--prod",
             "--dir", str(output_dir),
             "--site", site_id,
             "--auth", netlify_token,
             "--message", f"Recruitin: {campagne}"],
            capture_output=True, text=True, timeout=120
        )
        # Haal URL uit output
        for line in result.stdout.splitlines():
            if "Website URL" in line or "https://" in line:
                url = line.split()[-1].strip()
                if url.startswith("https://"):
                    print(f"   ✅ Live: {url}")
                    return url
    except Exception as e:
        print(f"   ❌ Netlify deploy fout: {e}")
    return None


def create_pipedrive_deal(template_vars: dict, live_url: str | None) -> str | None:
    """Maak Pipedrive deal aan met alle intake data. Geeft deal URL terug."""
    api_key = os.getenv("PIPEDRIVE_API_KEY", "")
    domain  = os.getenv("PIPEDRIVE_DOMAIN", "recruitin")

    if not api_key or api_key == "JOUW_PIPEDRIVE_API_KEY_HIER":
        print("   ⚠️  PIPEDRIVE_API_KEY niet ingesteld — deal skip")
        return None

    base = f"https://{domain}.pipedrive.com/api/v1"
    headers = {"Content-Type": "application/json"}

    functie = template_vars.get("{{FUNCTIE}}", "Onbekend")
    bedrijf = template_vars.get("{{BEDRIJF}}", "Onbekend bedrijf")
    email   = template_vars.get("{{CONTACT_EMAIL}}", "")
    regio   = template_vars.get("{{REGIO}}", "")
    sector  = template_vars.get("{{SECTOR}}", "")

    print(f"   📋 Pipedrive deal aanmaken: {functie} @ {bedrijf}...")

    try:
        # 1. Zoek of maak organisatie
        org_resp = requests.post(f"{base}/organizations", params={"api_token": api_key},
            json={"name": bedrijf}, timeout=10).json()
        org_id = org_resp.get("data", {}).get("id")

        # 2. Zoek of maak persoon
        person_resp = requests.post(f"{base}/persons", params={"api_token": api_key},
            json={"name": template_vars.get("{{CONTACT_NAAM}}", bedrijf),
                  "email": [email], "org_id": org_id}, timeout=10).json()
        person_id = person_resp.get("data", {}).get("id")

        # 3. Deal aanmaken
        note_tekst = (
            f"🚀 Recruitin Intake via Jotform\n"
            f"Functie: {functie}\n"
            f"Regio: {regio}\n"
            f"Sector: {sector}\n"
            f"Email: {email}\n"
        )
        if live_url:
            note_tekst += f"Landing page: {live_url}\n"

        deal_resp = requests.post(f"{base}/deals", params={"api_token": api_key},
            json={
                "title": f"{functie} — {bedrijf}",
                "org_id": org_id,
                "person_id": person_id,
                "stage_id": 215,  # Pipeline 15 Vacaturekanon: 🆕 Intake Ontvangen
            }, timeout=10).json()
        deal_id = deal_resp.get("data", {}).get("id")

        if deal_id:
            # Note toevoegen
            requests.post(f"{base}/notes", params={"api_token": api_key},
                json={"content": note_tekst, "deal_id": deal_id}, timeout=10)
            deal_url = f"https://{domain}.pipedrive.com/deal/{deal_id}"
            print(f"   ✅ Pipedrive deal #{deal_id}: {deal_url}")
            return deal_url

    except Exception as e:
        print(f"   ❌ Pipedrive fout: {e}")
    return None


def send_slack_notification(template_vars: dict, live_url: str | None,
                             pipedrive_url: str | None):
    """Stuur Slack notificatie met alle links en data."""
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        print("   ⚠️  SLACK_WEBHOOK_URL niet ingesteld")
        return

    functie = template_vars.get("{{FUNCTIE}}", "?")
    bedrijf = template_vars.get("{{BEDRIJF}}", "?")
    regio   = template_vars.get("{{REGIO}}", "?")
    sector  = template_vars.get("{{SECTOR}}", "?")
    email   = template_vars.get("{{CONTACT_EMAIL}}", "?")

    blocks = [
        {"type": "header", "text": {"type": "plain_text",
            "text": f"🚀 Nieuwe intake: {functie} @ {bedrijf}"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Functie:*\n{functie}"},
            {"type": "mrkdwn", "text": f"*Bedrijf:*\n{bedrijf}"},
            {"type": "mrkdwn", "text": f"*Regio:*\n{regio}"},
            {"type": "mrkdwn", "text": f"*Sector:*\n{sector}"},
            {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
        ]},
    ]

    actions = []
    if live_url:
        actions.append({"type": "button", "text": {"type": "plain_text",
            "text": "🌐 Bekijk landingspagina"}, "url": live_url, "style": "primary"})
    if pipedrive_url:
        actions.append({"type": "button", "text": {"type": "plain_text",
            "text": "📋 Open Pipedrive deal"}, "url": pipedrive_url})

    if actions:
        blocks.append({"type": "actions", "elements": actions})

    try:
        requests.post(webhook, json={"blocks": blocks}, timeout=5)
        print(f"   ✅ Slack notificatie verstuurd")
    except Exception as e:
        print(f"   ❌ Slack fout: {e}")


def generate_hero_image(functie: str, sector: str, out_dir: Path, dry_run: bool = False) -> str | None:
    """
    Genereert een 16:9 hero image via Kling text-to-image.
    Hergebruikt JWT auth + sector bg_hints uit kling_invideo_pipeline.py
    Fallback naar Unsplash als Kling niet beschikbaar is.
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from kling_invideo_pipeline import (
            SECTOR_MOTION, sector_to_slug, kling_headers, KLING_BASE,
            KLING_ACCESS_KEY
        )
    except ImportError as e:
        print(f"   ⚠️  Kling import mislukt: {e}")
        return None

    if not KLING_ACCESS_KEY:
        print("   ⚠️  KLING_ACCESS_KEY niet ingesteld — Kling hero skip")
        return None

    slug = sector_to_slug(sector) if sector else "productie"
    bg_hint = SECTOR_MOTION.get(slug, SECTOR_MOTION["productie"])["bg_hint"]

    prompt = (
        f"Professional recruitment hero image, {functie} vacancy, "
        f"{bg_hint}. Wide cinematic 16:9, Dutch corporate photography style, "
        f"confident professional person in work environment, no text, no watermarks, "
        f"photorealistic 4K, dramatic cinematic lighting, orange accent color #E8630A."
    )

    if dry_run:
        print(f"   [DRY RUN] Hero prompt: {prompt[:80]}...")
        return None

    print(f"   🎨 Kling hero image genereren voor '{functie}' ({slug})...")

    try:
        # Submit image generation job
        r = requests.post(
            f"{KLING_BASE}/v1/images/generations",
            headers=kling_headers(),
            json={
                "model_name": "kling-v1-5",
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "n": 1,
            },
            timeout=30,
        )
        data = r.json()
        task_id = data.get("data", {}).get("task_id")

        if not task_id:
            print(f"   ❌ Kling submit fout: {data.get('message', data)}")
            return None

        print(f"   ⏳ Kling job ingediend: {task_id}")

        # Poll tot klaar (max 5 min)
        for attempt in range(30):
            time.sleep(10)
            poll = requests.get(
                f"{KLING_BASE}/v1/images/generations/{task_id}",
                headers=kling_headers(),
                timeout=15,
            ).json()
            status = poll.get("data", {}).get("task_status", "")
            print(f"   ⏳ Status [{attempt+1}/30]: {status}")

            if status == "succeed":
                images = poll.get("data", {}).get("task_result", {}).get("images", [])
                if images:
                    img_url = images[0].get("url")
                    # Download lokaal
                    out_dir.mkdir(parents=True, exist_ok=True)
                    img_path = out_dir / "hero.jpg"
                    img_data = requests.get(img_url, timeout=60).content
                    img_path.write_bytes(img_data)
                    print(f"   ✅ Hero image opgeslagen: {img_path}")
                    return str(img_path)

            elif status in ("failed", "error"):
                print(f"   ❌ Kling image generatie mislukt")
                return None

        print("   ❌ Kling timeout na 5 minuten")
        return None

    except Exception as e:
        print(f"   ❌ Kling hero fout: {e}")
        return None


def fill_template(template_path: Path, vars: dict, branding: dict) -> str:
    html = template_path.read_text(encoding="utf-8")
    for key, val in branding.items():
        html = html.replace(key, val)
    for tag, val in vars.items():
        html = html.replace(tag, str(val))
    remaining = re.findall(r'\{\{[A-Z_]+\}\}', html)
    if remaining:
        print(f"⚠️ Niet-ingevulde tags: {set(remaining)}")
    return html


def print_report(jotform_data, template_vars):
    print("\n" + "═"*60)
    print("  DATA MAPPING RAPPORT")
    print("═"*60)
    print(f"\nJotform velden ({len(jotform_data)}):")
    for k, v in jotform_data.items():
        tag = FIELD_MAPPING.get(k.lower(), "—")
        status = "✓" if tag != "—" else "✗ niet gemapped"
        print(f"  {status}  {k}: {str(v)[:40]}  →  {tag}")
    print(f"\nTemplate variabelen ({len(template_vars)}):")
    for tag, val in sorted(template_vars.items()):
        is_default = val == DEFAULTS.get(tag)
        src = "(default)" if is_default else "(jotform)"
        print(f"  {tag}: {str(val)[:50]}  {src}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission-id", help="Jotform submission ID")
    parser.add_argument("--json-file",     help="JSON bestand met test data")
    parser.add_argument("--template",      default="/Users/wouterarts/recruitin/landing-pages/template/b2c_template.html")
    parser.add_argument("--output-dir",    default="/tmp/recruitin-local/b2c-landing-pages")
    parser.add_argument("--report",        action="store_true")
    parser.add_argument("--skip-kling",    action="store_true", help="Sla Kling hero generatie over (gebruik Unsplash fallback)")
    args = parser.parse_args()

    if args.json_file:
        jotform_data = json.loads(Path(args.json_file).read_text())
        print(f"✅ Test data geladen: {args.json_file}")
    elif args.submission_id:
        jotform_data = fetch_jotform_submission(args.submission_id)
    else:
        # Demo data met echte veldnamen
        jotform_data = {
            "q2_textbox0":  "Constructeur Werktuigbouw",
            "q3_textbox1":  "Gelderland",
            "q6_textarea4": "Als Constructeur ben je verantwoordelijk voor het ontwerpen van complexe machineonderdelen.\n- HBO Werktuigbouw of gelijkwaardig\n- 3+ jaar ervaring in SolidWorks\n- Kennis van normen en richtlijnen",
            "q7_textbox5":  "https://recruitin.nl/vacature/constructeur",
            "emailfor":     "wouter@recruitin.nl",
        }
        print("ℹ️  Demo data gebruikt (echte Jotform veldnamen)")

    template_vars = map_to_template_vars(jotform_data)
    bedrijf_url = jotform_data.get("website", "")
    bedrijf_naam = template_vars.get("{{BEDRIJF}}", "Recruitin klant")
    branding = get_branding(bedrijf_url, bedrijf_naam)

    # ── Kling hero image genereren ───────────────────────────────────────────
    functie = template_vars.get("{{FUNCTIE}}", "")
    sector  = detect_sector(functie)
    campagne_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', functie.lower()[:30]) or "campagne"
    hero_out_dir = Path(args.output_dir) / campagne_slug

    if not args.skip_kling:
        hero_path = generate_hero_image(functie, sector, hero_out_dir)
        if hero_path:
            # Relatief pad voor HTML (zelfde map als index.html)
            template_vars["{{HERO_IMAGE}}"] = "hero.jpg"
            print(f"   🖼️  Hero image → {{{{HERO_IMAGE}}}} = hero.jpg")
        else:
            # Fallback: Unsplash op basis van sector
            design = SECTOR_DESIGN.get(sector, SECTOR_DESIGN["default"])
            template_vars["{{HERO_IMAGE}}"] = design[2]
            print(f"   🖼️  Fallback hero → Unsplash ({sector})")
    else:
        print("   ⏭️  Kling hero overgeslagen (--skip-kling)")

    # Sector kleuren toepassen
    design = SECTOR_DESIGN.get(sector, SECTOR_DESIGN["default"])
    branding.setdefault("__BRAND_PRIMARY__", design[0])
    branding.setdefault("__BRAND_SECONDARY__", design[1])

    if args.report:
        print_report(jotform_data, template_vars)

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"❌ Template niet gevonden: {template_path}")
        sys.exit(1)

    html = fill_template(template_path, template_vars, branding)

    campagne = template_vars.get("{{CAMPAGNE}}", f"test_{datetime.now().strftime('%Y%m%d_%H%M')}")
    campagne = re.sub(r'[^a-zA-Z0-9_-]', '_', campagne)
    output_dir = Path(args.output_dir) / campagne
    output_dir.mkdir(parents=True, exist_ok=True)

    # Kopieer hero image naar output dir als het lokaal gegenereerd is
    if template_vars.get("{{HERO_IMAGE}}") == "hero.jpg" and hero_out_dir.exists():
        src = hero_out_dir / "hero.jpg"
        dst = output_dir / "hero.jpg"
        if src.exists() and src != dst:
            import shutil
            shutil.copy2(src, dst)

    output_file = output_dir / "index.html"
    output_file.write_text(html, encoding="utf-8")

    print(f"✅ Landingspagina gegenereerd: {output_file}")

    # ── POST-GENERATIE: Deploy + CRM + Notificatie ─────────────────────────
    if not getattr(args, 'skip_post', False):
        print("\n── POST-GENERATIE ─────────────────────────────────────────")
        live_url      = deploy_to_netlify(output_dir, campagne, sector)
        pipedrive_url = create_pipedrive_deal(template_vars, live_url)
        send_slack_notification(template_vars, live_url, pipedrive_url)
        if live_url:
            print(f"\n🌐 Live: {live_url}")

    print(f"   open '{output_file}'")

if __name__ == "__main__":
    main()
