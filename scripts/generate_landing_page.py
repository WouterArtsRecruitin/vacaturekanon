#!/usr/bin/env python3
"""
generate_landing_page.py
Recruitin B.V. — TAAK 2: Dynamische landing page genereren per sector

Gebruik:
  python3 generate_landing_page.py --sector "oil & gas" --regio "Gelderland" \
    --campagne KT_OilGas_202603 --jotform-url https://form.jotform.com/XXXX \
    [--deploy] [--netlify-token TOKEN]
"""

import os, sys, shutil, argparse, subprocess, json, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ── Config ───────────────────────────────────────────────────────────────────
# Cloud Ready: Verwijs root (recruitin) direct gerelateerd aan de plek van het script
BASE_DIR      = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
TEMPLATE_PATH = BASE_DIR / "landing-pages" / "template" / "index.html"
default_out   = Path(os.getenv("LOCAL_OUTPUT_BASE", "/tmp/recruitin-local"))
OUTPUT_BASE   = default_out / "landing-pages"

META_PIXEL_ID = os.getenv("META_PIXEL_ID", "238226887541404")
JOTFORM_URL   = os.getenv("JOTFORM_URL", "https://form.jotform.com/")
NETLIFY_TOKEN = os.getenv("NETLIFY_TOKEN", "")
SLACK_URL     = os.getenv("SLACK_WEBHOOK_URL", "")

# ── Sector data (SSOT) ───────────────────────────────────────────────────────
SECTOR_DATA = {
    "oil-gas": {
        "titel":     "Procesoperator",
        "schaarste": "8.5/10",
        "doorloop":  "5,2 mnd",
        "kosten":    "€21.400",
        "pijnpunt":  "productie-uitval en veiligheidsrisico's door onderbezetting",
        "stat1":     "73% van raffinaderijen heeft nu ≥1 kritieke vacature open",
        "emoji":     "⚙️",
        "netlify_site_id": os.getenv("NETLIFY_SITE_OIL_GAS", ""),
    },
    "constructie": {
        "titel":     "Uitvoerder / Calculator",
        "schaarste": "9.1/10",
        "doorloop":  "6,1 mnd",
        "kosten":    "€24.800",
        "pijnpunt":  "projectvertraging en boeteclausules door capaciteitstekort",
        "stat1":     "81% van bouwbedrijven mist deadlines door personeelstekort",
        "emoji":     "🏗️",
        "netlify_site_id": os.getenv("NETLIFY_SITE_CONSTRUCTIE", ""),
    },
    "automation": {
        "titel":     "PLC / SCADA Engineer",
        "schaarste": "9.4/10",
        "doorloop":  "7,0 mnd",
        "kosten":    "€28.200",
        "pijnpunt":  "stilstand van productielijnen en gemiste digitaliseringsprojecten",
        "stat1":     "Slechts 340 PLC Engineers beschikbaar voor 1.200+ vacatures in NL",
        "emoji":     "🤖",
        "netlify_site_id": os.getenv("NETLIFY_SITE_AUTOMATION", ""),
    },
    "productie": {
        "titel":     "Productie Teamleider",
        "schaarste": "7.8/10",
        "doorloop":  "4,5 mnd",
        "kosten":    "€18.600",
        "pijnpunt":  "verhoogde uitval en kwaliteitsproblemen door rotatiedruk",
        "stat1":     "68% van productiebedrijven draait op minimale bezetting",
        "emoji":     "🏭",
        "netlify_site_id": os.getenv("NETLIFY_SITE_PRODUCTIE", ""),
    },
    "renewable-energy": {
        "titel":     "Wind / Solar Technicus",
        "schaarste": "9.7/10",
        "doorloop":  "8,3 mnd",
        "kosten":    "€33.600",
        "pijnpunt":  "vertraging van energietransitie projecten",
        "stat1":     "Groei van 340% in vacatures, talent groeit slechts 40%",
        "emoji":     "🌱",
        "netlify_site_id": os.getenv("NETLIFY_SITE_RENEWABLE_ENERGY", ""),
    },
}

# ── Hulpfuncties ─────────────────────────────────────────────────────────────

def sector_to_slug(sector: str) -> str:
    """Normaliseert sector string naar URL-slug."""
    mapping = {
        "oil & gas":        "oil-gas",
        "oil and gas":      "oil-gas",
        "constructie":      "constructie",
        "bouw":             "constructie",
        "automation":       "automation",
        "automatisering":   "automation",
        "productie":        "productie",
        "manufacturing":    "productie",
        "renewable energy": "renewable-energy",
        "renewable":        "renewable-energy",
        "energie":          "renewable-energy",
    }
    return mapping.get(sector.lower().strip(), sector.lower().replace(" ", "-").replace("&", ""))


def slack_notify(msg: str):
    if not SLACK_URL:
        print(f"[SLACK SKIPPED] {msg}")
        return
    try:
        requests.post(SLACK_URL, json={"text": msg}, timeout=5)
    except Exception as e:
        print(f"[SLACK ERROR] {e}")


def check_subdomain_live(slug: str) -> bool:
    """Geeft True als subdomain al live is (via curl - HTTP 200)."""
    url = f"https://{slug}.vacaturekanon.nl"
    try:
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url], 
                           capture_output=True, text=True, timeout=8)
        return r.stdout.strip() == "200"
    except Exception:
        return False


def generate_html(slug: str, sector_display: str, regio: str,
                  campagne_naam: str, jotform_url: str) -> str:
    """Vult het HTML template in met sector-specifieke data."""
    data = SECTOR_DATA.get(slug)
    if not data:
        print(f"⚠️ Waarschuwing: Onbekende sector '{slug}'. Gebruik generieke fallback data.")
        data = {
            "titel":     f"Technisch Specialist ({sector_display})",
            "schaarste": "8.0/10",
            "doorloop":  "5,0 mnd",
            "kosten":    "€20.000",
            "pijnpunt":  "capaciteitsproblemen en vertraagde projecten",
            "stat1":     "Meer dan 65% van bedrijven in deze sector heeft een tekort",
            "emoji":     "💼",
            "netlify_site_id": ""
        }

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    replacements = {
        "{{TITEL}}":        data["titel"],
        "{{SECTOR}}":       sector_display,
        "{{SECTOR_SLUG}}":  slug,
        "{{REGIO}}":        regio,
        "{{SCHAARSTE}}":    data["schaarste"],
        "{{DOORLOOP}}":     data["doorloop"],
        "{{KOSTEN}}":       data["kosten"],
        "{{PIJNPUNT}}":     data["pijnpunt"],
        "{{STAT1}}":        data["stat1"],
        "{{EMOJI}}":        data["emoji"],
        "{{CAMPAGNE_NAAM}}": campagne_naam,
        "{{META_PIXEL_ID}}": META_PIXEL_ID,
        "{{JOTFORM_URL}}":  jotform_url or JOTFORM_URL,
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    return template


def save_html(html: str, campagne_naam: str, slug: str) -> Path:
    out_dir = OUTPUT_BASE / campagne_naam
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")
    
    # Tijdelijke deploy directory (volgens master prompt v2)
    tmp_dir = Path(f"/tmp/lp-{slug}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_file = tmp_dir / "index.html"
    tmp_file.write_text(html, encoding="utf-8")
    
    print(f"✅ HTML opgeslagen: {out_file} (deploy staging {tmp_dir})")
    return tmp_dir


def deploy_netlify(deploy_dir: Path, slug: str, campagne_naam: str,
                   token: str = None) -> str | None:
    """Deploy naar Netlify via CLI. Geeft live URL terug."""
    token = token or NETLIFY_TOKEN
    if not token:
        print("⚠️  NETLIFY_TOKEN niet ingesteld — skip deploy")
        return None

    data = SECTOR_DATA.get(slug, {})
    site_id = data.get("netlify_site_id", "")

    env = {**os.environ, "NETLIFY_AUTH_TOKEN": token}

    if site_id:
        # Bestaande site updaten
        cmd = [
            "netlify", "deploy", "--prod",
            f"--dir={deploy_dir}",
            f"--site={site_id}",
            "--json",
        ]
    else:
        # Nieuwe site aanmaken
        site_name = f"kt-{slug}"
        print(f"🆕 Nieuwe Netlify site aanmaken: {site_name}")
        try:
            create_r = requests.post(
                "https://api.netlify.com/api/v1/sites",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": site_name,
                    "custom_domain": f"{slug}.vacaturekanon.nl",
                },
                timeout=15,
            )
            new_site = create_r.json()
            new_site_id = new_site.get("id", "")
            if new_site_id:
                print(f"   Site ID: {new_site_id}")
                # Sla site ID op in .env
                env_path = BASE_DIR / ".env"
                env_key = f"NETLIFY_SITE_{slug.upper().replace('-', '_')}"
                with open(env_path, "a") as f:
                    f.write(f"\n{env_key}={new_site_id}")
                print(f"   Opgeslagen als {env_key} in .env")
                site_id = new_site_id
            else:
                print(f"   ⚠️  Site aanmaken gaf geen ID: {new_site}")
        except Exception as e:
            print(f"   ❌ Site aanmaken mislukt: {e}")
            return None

        cmd = [
            "netlify", "deploy", "--prod",
            f"--dir={deploy_dir}",
            f"--site={site_id}",
            "--json",
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        if result.returncode == 0:
            output = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {}
            url = output.get("deploy_url") or output.get("url") or f"https://{slug}.vacaturekanon.nl"
            print(f"✅ Netlify deploy klaar: {url}")
            return url
        else:
            print(f"❌ Netlify deploy fout:\n{result.stderr}")
            # Fallback: probeer Vercel
            return deploy_vercel_fallback(deploy_dir, slug)
    except subprocess.TimeoutExpired:
        print("❌ Netlify deploy timeout")
        return None
    except FileNotFoundError:
        print("❌ Netlify CLI niet gevonden — installeer via: npm install -g netlify-cli")
        return None


def deploy_vercel_fallback(deploy_dir: Path, slug: str) -> str | None:
    """Fallback deploy naar Vercel als Netlify faalt."""
    print("🔄 Fallback naar Vercel...")
    try:
        result = subprocess.run(
            ["npx", "vercel", "--prod", "--yes", str(deploy_dir)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            url = next((l for l in reversed(lines) if l.startswith("https://")), None)
            print(f"✅ Vercel fallback deploy klaar: {url}")
            return url
        else:
            print(f"❌ Vercel ook mislukt:\n{result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Vercel fallback error: {e}")
        return None


# ── Main ─────────────────────────────────────────────────────────────────────

def run(sector: str, regio: str, campagne_naam: str, deploy: bool = False,
        jotform_url: str = None, netlify_token: str = None,
        force: bool = False) -> str | None:
    """
    Hoofdfunctie. Retourneert de live URL of None bij fout.
    """
    slug = sector_to_slug(sector)
    sector_display = sector.title()

    print(f"\n── TAAK 2: Landing Page ──────────────────")
    print(f"   Sector:   {sector} → {slug}")
    print(f"   Regio:    {regio}")
    print(f"   Campagne: {campagne_naam}")
    print(f"   Deploy:   {'ja' if deploy else 'nee (lokaal opslaan)'}")
    print()

    # Check of subdomain al live is
    if not force and check_subdomain_live(slug):
        live_url = f"https://{slug}.vacaturekanon.nl"
        print(f"ℹ️  Subdomain al live: {live_url} — skip deploy, ga naar TAAK 3")
        return live_url

    # HTML genereren en opslaan
    try:
        html = generate_html(slug, sector_display, regio, campagne_naam, jotform_url)
        out_dir = save_html(html, campagne_naam, slug)
    except ValueError as e:
        print(f"❌ {e}")
        return None

    # Deployen
    live_url = None
    if deploy:
        live_url = deploy_netlify(out_dir, slug, campagne_naam, netlify_token)
        if live_url:
            slack_notify(f"🌐 {campagne_naam} — Landing page live: https://{slug}.kandidatentekort.nl")
    else:
        print(f"📁 Lokaal opgeslagen (geen deploy): {out_dir}/index.html")
        live_url = f"https://{slug}.vacaturekanon.nl"

    return live_url


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recruitin Landing Page Generator")
    parser.add_argument("--sector",        required=True, help='bijv. "oil & gas"')
    parser.add_argument("--regio",         default="Gelderland")
    parser.add_argument("--campagne",      required=True, help="bijv. KT_OilGas_202603")
    parser.add_argument("--jotform-url",   default=None,  help="Jotform embed URL")
    parser.add_argument("--netlify-token", default=None)
    parser.add_argument("--deploy",        action="store_true", help="Deploy naar Netlify")
    parser.add_argument("--force",         action="store_true", help="Herbouw ook als subdomain al live is")
    args = parser.parse_args()

    url = run(
        sector        = args.sector,
        regio         = args.regio,
        campagne_naam = args.campagne,
        deploy        = args.deploy,
        jotform_url   = args.jotform_url,
        netlify_token = args.netlify_token,
        force         = args.force,
    )
    if url:
        print(f"\n🌐 URL: {url}")
