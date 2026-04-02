#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   VACATUREKANON ORCHESTRATOR v2.0                                        ║
║   Recruitin B.V. | Wouter Arts                                           ║
║                                                                          ║
║   Alles-in-één systeem:                                                  ║
║   Jotform → Imagen 4 Hero Image → HTML → GitHub → Netlify → Live        ║
║                                                                          ║
║   Modi:                                                                  ║
║     python3 vacaturekanon_v2.py --setup       # Systeem initialiseren   ║
║     python3 vacaturekanon_v2.py --webhook     # Webhook server starten  ║
║     python3 vacaturekanon_v2.py --generate    # Handmatig genereren     ║
║     python3 vacaturekanon_v2.py --test        # Test met demo data      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import base64
import argparse
import threading
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATIE
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent

# Laad .env
_env_file = SCRIPT_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

CONFIG = {
    "gemini_api_key":  os.getenv("GEMINI_API_KEY", "AIzaSyAMrLSj559iE6daAWCmY1u0zIXyGzFqlZ8"),
    "github_token":    os.getenv("GITHUB_TOKEN",   "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"),
    "github_repo":     os.getenv("GITHUB_REPO",    "WouterArtsRecruitin/vacaturekanon-landing-pages"),
    "netlify_hook":    os.getenv("NETLIFY_HOOK_URL", ""),
    "imagen_model":    os.getenv("IMAGEN_MODEL",   "imagen-4.0-fast-generate-001"),
    "webhook_port":    int(os.getenv("WEBHOOK_PORT", "5055")),
}

# MCP Servers (uit bestaande orchestrator)
MCP_SERVERS = [
    ("Zapier",          "https://mcp.zapier.com/api/mcp/a/23866051/mcp"),
    ("Jotform",         "https://mcp.jotform.com"),
    ("Notion",          "https://mcp.notion.com/mcp"),
    ("Canva",           "https://mcp.canva.com/mcp"),
    ("Figma",           "https://mcp.figma.com/mcp"),
    ("Invideo",         "https://mcp.invideo.io/sse"),
    ("Apollo.io",       "https://mcp.apollo.io/mcp"),
    ("Gmail",           "https://gmail.mcp.claude.com/mcp"),
    ("Google Sheets",   "https://mcp.supermetrics.com/mcp"),
    ("Google Calendar", "https://gcal.mcp.claude.com/mcp"),
    ("Slack",           "https://mcp.slack.com/mcp"),
    ("Clay",            "https://api.clay.com/v3/mcp"),
    ("Supabase",        "https://mcp.supabase.com/mcp"),
]

# Sector → Imagen 4 prompt library
SECTOR_PROMPTS = {
    "constructie": (
        "Cinematic professional recruitment photography. Dutch male construction foreman, "
        "early 40s, dark brown hair neatly combed, light beard, strong jawline. "
        "Dark navy work jacket, bright orange high-vis vest, yellow hard hat. "
        "Standing confidently on large industrial construction site at golden hour. "
        "Steel structures, cranes in background soft bokeh. 85mm lens. "
        "No text, no watermarks. Photorealistic."
    ),
    "oil_gas": (
        "Cinematic professional recruitment photography. Dutch male EPC engineer, "
        "early 40s, trimmed beard. Orange high-vis jacket, safety glasses. "
        "Standing at industrial oil refinery at sunset. "
        "Large pipes, tanks, industrial platform. Dramatic warm lighting. "
        "No text, no watermarks. Photorealistic."
    ),
    "productie": (
        "Cinematic professional recruitment photography. Dutch male production manager, "
        "early 40s, confident expression. Company polo, safety gear. "
        "Modern factory floor with CNC machines in background bokeh. "
        "Professional studio lighting. No text. Photorealistic."
    ),
    "automation": (
        "Cinematic professional recruitment photography. Dutch male automation engineer, "
        "early 40s, clean-cut. Dark workwear. Control room or automation panel "
        "with screens and equipment. HMI display visible. Confident pose. "
        "No text, no watermarks. Photorealistic."
    ),
    "renewable": (
        "Cinematic professional recruitment photography. Dutch male renewable energy technician, "
        "early 40s. Safety harness and wind energy gear. Wind turbines at golden hour "
        "Dutch landscape, dramatic clouds. Wide angle. "
        "No text, no watermarks. Photorealistic."
    ),
    "default": (
        "Cinematic professional recruitment photography. Dutch male skilled industrial worker, "
        "early 40s, dark hair, light beard. Professional work attire and safety gear. "
        "Industrial work environment, bokeh background. Golden hour lighting. "
        "No text, no watermarks. Photorealistic."
    ),
}

# Sector accent kleuren
SECTOR_COLORS = {
    "constructie": "#f97316",
    "oil_gas":     "#0ea5e9",
    "productie":   "#10b981",
    "automation":  "#6366f1",
    "renewable":   "#22c55e",
    "default":     "#f97316",
}

# Jotform veld schema (25 fields, uit bestaande orchestrator uitgebreid)
JOTFORM_FIELDS = {
    "Sectie 1 — Bedrijf": {
        "q3_bedrijfsnaam":      ("Bedrijfsnaam",          "text",     True),
        "q4_bedrijfsnaamKort":  ("Logo letter(s)",         "text",     False),
        "q5_tagline":           ("Tagline",                "text",     False),
        "q6_overBedrijf":       ("Over het bedrijf",       "textarea", True),
        "q7_website":           ("Website URL",            "text",     False),
        "q8_sector":            ("Sector",                 "dropdown", True),
        "q9_accentKleur":       ("Accent kleur (hex)",     "text",     False),
        "q10_opgericht":        ("Opgericht (jaar)",        "text",     False),
        "q11_medewerkers":      ("Aantal medewerkers",     "text",     False),
    },
    "Sectie 2 — Vacature": {
        "q13_functietitel":     ("Functietitel",           "text",     True),
        "q14_locatie":          ("Locatie",                "text",     True),
        "q15_dienstverband":    ("Dienstverband",          "dropdown", True),
        "q16_heroIntro":        ("Hero intro tekst",       "textarea", False),
    },
    "Sectie 3 — Functie": {
        "q17_taken":            ("Taken (1 per regel)",    "textarea", True),
        "q18_eisen":            ("Eisen (1 per regel)",    "textarea", True),
    },
    "Sectie 4 — Arbeidsvoorwaarden": {
        "q19_salaris":          ("Salaris range",          "text",     False),
        "q20_benefits":         ("Benefits (1 per regel)", "textarea", True),
    },
    "Sectie 5 — Sollicitatie": {
        "q21_hrEmail":          ("HR E-mailadres",         "email",    True),
        "q22_hrTelefoon":       ("HR Telefoon",            "text",     False),
        "q23_careersUrl":       ("Careers pagina URL",     "text",     False),
        "q24_jotformId":        ("Jotform sollicitatie ID","text",     False),
    },
    "Sectie 6 — Statistieken (optioneel)": {
        "q25_stat1Waarde":      ("Statistiek 1 waarde",   "text",     False),
        "q26_stat1Label":       ("Statistiek 1 label",    "text",     False),
        "q27_stat2Waarde":      ("Statistiek 2 waarde",   "text",     False),
        "q28_stat2Label":       ("Statistiek 2 label",    "text",     False),
        "q29_stat3Waarde":      ("Statistiek 3 waarde",   "text",     False),
        "q30_stat3Label":       ("Statistiek 3 label",    "text",     False),
        "q31_stat4Waarde":      ("Statistiek 4 waarde",   "text",     False),
        "q32_stat4Label":       ("Statistiek 4 label",    "text",     False),
    },
}

# Email sequences (uit bestaande orchestrator)
EMAIL_SEQUENCES = {
    "bevestiging": {
        "name":    "Formulier ontvangen",
        "trigger": "form_submission",
        "delay":   "direct",
        "subject": "✅ Bedankt! Vacaturekanon ontving je aanvraag voor {functietitel}",
        "body":    "Je aanvraag voor {functietitel} bij {bedrijfsnaam} is ontvangen. We genereren nu de landingspagina (±2 min). Je ontvangt zodra de pagina live is een tweede e-mail met de preview link.",
    },
    "page_live": {
        "name":    "Pagina Live",
        "trigger": "page_deployed",
        "delay":   "±2 min na formulier",
        "subject": "🚀 Landingspagina live: {functietitel} | {bedrijfsnaam}",
        "body":    "De vacaturelandingspagina is live!\n\nPreview: {preview_url}\n\nDe pagina is nu ook in GitHub: {github_url}",
    },
    "meta_reminder": {
        "name":    "Meta Campagne Herinnering",
        "trigger": "page_live + 1 dag",
        "subject": "📢 Klaar om te adverteren? Meta campagne voor {functietitel}",
        "body":    "De landingspagina {preview_url} is live. Tijd om Meta advertenties te activeren.",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# LOGGER
# ═══════════════════════════════════════════════════════════════════════════

class Log:
    @staticmethod
    def header(msg):  print(f"\n{'═'*65}\n  {msg}\n{'═'*65}")
    @staticmethod
    def ok(msg):      print(f"  ✅ {msg}")
    @staticmethod
    def info(msg):    print(f"  ℹ️  {msg}")
    @staticmethod
    def warn(msg):    print(f"  ⚠️  {msg}")
    @staticmethod
    def err(msg):     print(f"  ❌ {msg}")
    @staticmethod
    def step(n, msg): print(f"\n📍 Stap {n}: {msg}")


# ═══════════════════════════════════════════════════════════════════════════
# IMAGE GENERATION — Imagen 4
# ═══════════════════════════════════════════════════════════════════════════

def generate_hero_image(sector: str, extra_prompt: str = "") -> bytes:
    """Genereer hero image via Google Imagen 4"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai niet geïnstalleerd. Run: pip install google-genai")

    if not CONFIG["gemini_api_key"]:
        raise ValueError("GEMINI_API_KEY niet ingesteld in .env")

    prompt = SECTOR_PROMPTS.get(sector, SECTOR_PROMPTS["default"])
    if extra_prompt:
        prompt = f"{prompt} {extra_prompt}"

    print(f"  🎨 Imagen 4 genereren (sector={sector})...")
    client = genai.Client(api_key=CONFIG["gemini_api_key"])
    response = client.models.generate_images(
        model=CONFIG["imagen_model"],
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9")
    )
    img_bytes = response.generated_images[0].image.image_bytes
    print(f"  ✅ Hero image: {len(img_bytes):,} bytes")
    return img_bytes


# ═══════════════════════════════════════════════════════════════════════════
# GITHUB
# ═══════════════════════════════════════════════════════════════════════════

def github_get_sha(path: str) -> str | None:
    url = f"https://api.github.com/repos/{CONFIG['github_repo']}/contents/{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {CONFIG['github_token']}"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r).get("sha")
    except Exception:
        return None


def github_push(path: str, content: bytes, message: str) -> str:
    url = f"https://api.github.com/repos/{CONFIG['github_repo']}/contents/{path}"
    sha = github_get_sha(path)
    payload = {"message": message, "content": base64.b64encode(content).decode()}
    if sha:
        payload["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="PUT",
        headers={"Authorization": f"token {CONFIG['github_token']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["content"]["download_url"]


# ═══════════════════════════════════════════════════════════════════════════
# HTML BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def darken(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"#{max(0,int(r*.88)):02x}{max(0,int(g*.88)):02x}{max(0,int(b*.88)):02x}"


def build_html(data: dict, hero_url: str) -> str:
    """Bouw de volledige landingspagina HTML"""

    bedrijf      = data.get("bedrijfsnaam", "Bedrijf")
    logo_letter  = data.get("bedrijfsnaam_kort", bedrijf[0]).strip()[0].upper()
    logo_rest    = bedrijf[1:] if not data.get("bedrijfsnaam_kort") else bedrijf
    tagline      = data.get("tagline", f"Werk bij {bedrijf}")
    over         = data.get("over_bedrijf", "").replace("\n", "<br>")
    website      = data.get("website", "#")
    sector       = data.get("sector", "constructie")
    accent       = data.get("accent_kleur", SECTOR_COLORS.get(sector, "#f97316"))
    accent_dk    = darken(accent)
    hero_dark    = "#0f172a"

    functie      = data.get("functietitel", "Vacature")
    locatie      = data.get("locatie", "Nederland")
    dienst       = data.get("dienstverband", "Fulltime")
    intro        = data.get("hero_intro", f"Word onderdeel van {bedrijf} en draag bij aan uitdagende projecten.")

    taken        = data.get("taken", [])
    eisen        = data.get("eisen", [])
    benefits_raw = data.get("benefits", [])
    stats        = data.get("stats", [])
    proces       = data.get("sollicitatieproces", [
        {"nr":"1","titel":"Solliciteer",  "tekst":f"Stuur je CV naar {data.get('hr_email','')}","tijd":"~1 dag"},
        {"nr":"2","titel":"Kennismaking", "tekst":"Telefonisch kennismakingsgesprek (±15 min)","tijd":"~3 dagen"},
        {"nr":"3","titel":"Gesprek",      "tekst":"Face-to-face gesprek en rondleiding","tijd":"~1 week"},
        {"nr":"4","titel":"Aanbieding",   "tekst":f"Welkom bij {bedrijf}! Onboarding en start","tijd":"~2-3 weken"},
    ])

    hr_email     = data.get("hr_email", "")
    hr_tel       = data.get("hr_telefoon", "")
    careers_url  = data.get("careers_url", f"{website}/careers")
    jotform_id   = data.get("jotform_id", "")

    # HTML sub-builders
    def li_list(items):
        return "".join(f'<li><span class="check">✓</span>{i}</li>' for i in items)

    def stats_html():
        icons = ["🏭","👥","🏆","🌍","📅","⭐"]
        out = ""
        for i, s in enumerate(stats[:4]):
            out += f"""<div class="stat-card">
              <div class="stat-icon">{icons[i%len(icons)]}</div>
              <div class="stat-num">{s.get("waarde","")}</div>
              <div class="stat-label">{s.get("label","")}</div>
            </div>"""
        return out

    def benefits_html():
        icons = ["💰","🚗","📚","🛡️","🤝","🌍","⚡","🌱"]
        out = ""
        for i, b in enumerate(benefits_raw[:8]):
            icon = b.get("icon", icons[i % len(icons)])
            out += f"""<div class="benefit-card">
              <div class="benefit-icon">{icon}</div>
              <h4>{b.get("titel","")}</h4>
              <p>{b.get("tekst","")}</p>
            </div>"""
        return out

    def proces_html():
        out = ""
        for i, s in enumerate(proces):
            cls = "active" if i == 0 else "inactive"
            out += f"""<div class="proces-step">
              <div class="proces-nr {cls}">{s.get("nr",i+1)}</div>
              <h4>{s.get("titel","")}</h4>
              <p>{s.get("tekst","")}</p>
              <div class="tijd">{s.get("tijd","")}</div>
            </div>"""
        return out

    def form_html():
        if jotform_id:
            return f'<a href="https://form.jotform.com/{jotform_id}" target="_blank" rel="noopener noreferrer" class="btn-primary" style="width:100%;justify-content:center;">✉️ Solliciteer Nu</a>'
        subj = urllib.parse.quote(f"Sollicitatie {functie} - {bedrijf}")
        return f'<a href="mailto:{hr_email}?subject={subj}" class="btn-primary" style="width:100%;justify-content:center;">✉️ Solliciteer Nu</a>'

    tel_html = (f'<a href="tel:{hr_tel.replace(" ","")}" class="contact-row">'
                f'<div class="contact-icon">📞</div>'
                f'<div><small>Telefoon</small><strong>{hr_tel}</strong></div></a>') if hr_tel else ""

    year = datetime.now().year

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{functie} Vacature | {bedrijf}</title>
  <meta name="description" content="{bedrijf} zoekt een {functie} in {locatie}. {intro[:120]}">
  <meta property="og:title" content="{functie} | {bedrijf}">
  <meta property="og:description" content="{intro[:200]}">
  <meta property="og:image" content="{hero_url}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{
      --bg:#FFFFFF;--fg:#0f172a;--muted:#64748b;--muted-bg:#f8fafc;
      --accent:{accent};--accent-dk:{accent_dk};--dark:{hero_dark};
      --border:#e2e8f0;--radius:12px;
    }}
    html{{scroll-behavior:smooth}}
    body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--fg)}}
    .container{{max-width:1200px;margin:0 auto;padding:0 1.5rem}}
    /* HEADER */
    header{{position:fixed;top:0;left:0;right:0;z-index:50;background:rgba(15,23,42,.95);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.08)}}
    .header-inner{{display:flex;align-items:center;justify-content:space-between;height:72px}}
    .logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.25rem;color:white;text-decoration:none}}
    .logo-accent{{color:var(--accent)}}
    .nav-links{{display:flex;align-items:center;gap:2rem;list-style:none}}
    .nav-links a{{font-size:.875rem;font-weight:500;color:rgba(255,255,255,.7);text-decoration:none;transition:color .2s}}
    .nav-links a:hover{{color:white}}
    .btn-nav{{background:var(--accent);color:white;padding:10px 20px;border-radius:8px;font-size:.875rem;font-weight:600;text-decoration:none;transition:background .2s}}
    .btn-nav:hover{{background:var(--accent-dk)}}
    /* HERO */
    #hero{{position:relative;min-height:100vh;display:flex;align-items:center;overflow:hidden}}
    .hero-bg{{position:absolute;inset:0}}
    .hero-bg img{{width:100%;height:100%;object-fit:cover;object-position:center top}}
    .hero-bg-overlay{{position:absolute;inset:0;background:linear-gradient(135deg,rgba(10,18,35,.85) 0%,rgba(15,30,55,.6) 60%,rgba(10,18,35,.45) 100%)}}
    .hero-fade{{position:absolute;bottom:0;left:0;right:0;height:120px;background:linear-gradient(to top,var(--bg),transparent);z-index:2}}
    .hero-content{{position:relative;z-index:3;padding:9rem 0 6rem;max-width:780px}}
    .hero-badge{{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;border-radius:100px;background:rgba(249,115,22,.15);backdrop-filter:blur(4px);margin-bottom:1.5rem}}
    .hero-badge .dot{{width:8px;height:8px;border-radius:50%;background:var(--accent)}}
    .hero-badge span{{font-size:.875rem;font-weight:500;color:white}}
    h1{{font-family:'Space Grotesk',sans-serif;font-size:clamp(3rem,7vw,5rem);font-weight:700;line-height:1.05;color:white;margin-bottom:1.5rem;letter-spacing:-1px}}
    .hero-sub{{font-size:1.2rem;color:rgba(255,255,255,.75);line-height:1.7;margin-bottom:2rem;max-width:580px}}
    .hero-location{{display:flex;align-items:center;gap:8px;color:rgba(255,255,255,.6);font-size:.9rem;margin-bottom:2.5rem}}
    .hero-ctas{{display:flex;gap:1rem;flex-wrap:wrap}}
    .btn-primary{{display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:white;padding:14px 28px;border-radius:8px;font-size:1rem;font-weight:600;text-decoration:none;transition:background .2s,transform .15s;box-shadow:0 4px 16px rgba(249,115,22,.4)}}
    .btn-primary:hover{{background:var(--accent-dk);transform:translateY(-1px)}}
    .btn-outline{{display:inline-flex;align-items:center;gap:8px;border:1.5px solid rgba(255,255,255,.3);color:white;padding:14px 28px;border-radius:8px;font-size:1rem;font-weight:500;text-decoration:none;transition:border-color .2s,background .2s}}
    .btn-outline:hover{{border-color:rgba(255,255,255,.7);background:rgba(255,255,255,.08)}}
    /* SECTIONS */
    section{{padding:6rem 0}}
    .section-label{{display:block;font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;color:var(--accent);margin-bottom:1rem}}
    h2{{font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,4vw,3rem);font-weight:700;color:var(--fg);line-height:1.15;letter-spacing:-.5px;margin-bottom:1.25rem}}
    h2 .accent{{color:var(--accent)}}
    .section-sub{{font-size:1.05rem;color:var(--muted);line-height:1.75;max-width:600px}}
    /* OVER ONS */
    .overons-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:start;margin-top:3.5rem}}
    .overons-text p{{font-size:.95rem;line-height:1.8;color:#475569;margin-bottom:1.25rem}}
    .stats-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
    .stat-card{{background:var(--muted-bg);border:1px solid var(--border);border-radius:var(--radius);padding:1.5rem}}
    .stat-icon{{font-size:1.5rem;margin-bottom:.75rem}}
    .stat-num{{font-family:'Space Grotesk',sans-serif;font-size:1.75rem;font-weight:700;color:var(--fg)}}
    .stat-label{{font-size:.8rem;color:var(--muted);margin-top:2px}}
    /* FUNCTIE */
    #de-functie{{background:var(--muted-bg)}}
    .functie-header{{text-align:center;margin-bottom:3rem}}
    .functie-header .section-sub{{margin:0 auto;text-align:center}}
    .functie-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2rem}}
    .functie-card{{background:white;border:1px solid var(--border);border-radius:var(--radius);padding:2rem;box-shadow:0 1px 4px rgba(0,0,0,.05)}}
    .functie-card h3{{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:700;color:var(--fg);margin-bottom:1.5rem}}
    .functie-list{{list-style:none}}
    .functie-list li{{display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);font-size:.9rem;line-height:1.6;color:#475569}}
    .functie-list li:last-child{{border-bottom:none}}
    .check{{color:var(--accent);font-weight:700;flex-shrink:0;margin-top:1px}}
    /* BENEFITS */
    #aanbod{{background:var(--dark)}}
    #aanbod h2{{color:white}}
    #aanbod .section-label{{color:rgba(249,115,22,.85)}}
    .benefits-header{{text-align:center;margin-bottom:3rem}}
    .benefits-header .section-sub{{margin:0 auto;text-align:center;color:rgba(255,255,255,.55)}}
    .benefits-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}}
    .benefit-card{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:var(--radius);padding:1.5rem;transition:background .2s,transform .2s}}
    .benefit-card:hover{{background:rgba(249,115,22,.08);border-color:rgba(249,115,22,.25);transform:translateY(-3px)}}
    .benefit-card h4{{font-family:'Space Grotesk',sans-serif;font-size:.95rem;font-weight:700;color:white;margin-bottom:.4rem}}
    .benefit-card p{{font-size:.82rem;color:rgba(255,255,255,.45);line-height:1.6}}
    .benefit-icon{{font-size:1.5rem;margin-bottom:.75rem}}
    /* PROCES */
    #sollicitatieproces{{background:var(--muted-bg)}}
    .proces-steps{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;position:relative;margin-top:3rem}}
    .proces-line{{position:absolute;top:28px;left:12.5%;right:12.5%;height:2px;background:linear-gradient(to right,var(--accent),rgba(249,115,22,.3));z-index:0}}
    .proces-step{{text-align:center;padding:0 1rem;position:relative;z-index:1}}
    .proces-nr{{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1.25rem;font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.2rem}}
    .active{{background:var(--accent);color:white;box-shadow:0 4px 16px rgba(249,115,22,.4)}}
    .inactive{{background:white;border:2px solid var(--accent);color:var(--accent)}}
    .proces-step h4{{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:700;color:var(--fg);margin-bottom:.5rem}}
    .proces-step p{{font-size:.83rem;color:var(--muted);line-height:1.6}}
    .tijd{{margin-top:.75rem;font-size:.72rem;color:var(--accent);font-weight:600}}
    /* SOLLICITEREN */
    .apply-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;margin-top:3rem}}
    .apply-contact{{background:white;border:1px solid var(--border);border-radius:var(--radius);padding:2rem}}
    .apply-contact h3{{font-family:'Space Grotesk',sans-serif;font-size:1.15rem;font-weight:700;color:var(--fg);margin-bottom:1.5rem}}
    .contact-row{{display:flex;align-items:center;gap:1rem;padding:1rem 0;border-bottom:1px solid var(--border);text-decoration:none;color:var(--fg);transition:color .2s}}
    .contact-row:last-child{{border-bottom:none}}
    .contact-row:hover{{color:var(--accent)}}
    .contact-icon{{width:44px;height:44px;border-radius:10px;background:rgba(249,115,22,.1);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.1rem}}
    .contact-row small{{display:block;font-size:.72rem;color:var(--muted)}}
    .contact-row strong{{font-weight:600;font-size:.9rem}}
    .apply-cta{{background:var(--dark);border-radius:var(--radius);padding:2.5rem;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
    .apply-cta h4{{font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;color:white;margin-bottom:.75rem}}
    .apply-cta p{{font-size:.9rem;color:rgba(255,255,255,.6);line-height:1.7;margin-bottom:2rem}}
    /* FOOTER */
    footer{{background:var(--dark);color:white;padding:3rem 0;border-top:1px solid rgba(255,255,255,.06)}}
    .footer-inner{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1.5rem}}
    .footer-logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.1rem;color:white}}
    .footer-links{{display:flex;gap:1.5rem}}
    .footer-links a{{font-size:.82rem;color:rgba(255,255,255,.55);text-decoration:none;transition:color .2s}}
    .footer-links a:hover{{color:var(--accent)}}
    .footer-copy{{font-size:.8rem;color:rgba(255,255,255,.4)}}
    @media(max-width:900px){{
      .overons-grid,.functie-grid,.apply-grid{{grid-template-columns:1fr}}
      .benefits-grid,.proces-steps{{grid-template-columns:1fr 1fr}}
      .nav-links{{display:none}}
    }}
  </style>
</head>
<body>
<header>
  <div class="container header-inner">
    <a href="#" class="logo"><span class="logo-accent">{logo_letter}</span>{logo_rest[1:]}<span class="logo-accent">.</span></a>
    <ul class="nav-links">
      <li><a href="#over-ons">Over Ons</a></li>
      <li><a href="#de-functie">De Functie</a></li>
      <li><a href="#aanbod">Aanbod</a></li>
    </ul>
    <a href="#solliciteren" class="btn-nav">Solliciteren</a>
  </div>
</header>

<section id="hero">
  <div class="hero-bg">
    <img src="{hero_url}" alt="{functie} bij {bedrijf}" />
    <div class="hero-bg-overlay"></div>
  </div>
  <div class="hero-fade"></div>
  <div class="container">
    <div class="hero-content">
      <div class="hero-badge"><span class="dot"></span><span>Vacature · Nu beschikbaar</span></div>
      <h1>{functie}<br><span class="logo-accent">{logo_letter}</span>{logo_rest[1:]}<span class="logo-accent">.</span></h1>
      <p class="hero-sub">{intro}</p>
      <div class="hero-location">📍 {locatie} &bull; {dienst}</div>
      <div class="hero-ctas">
        <a href="#solliciteren" class="btn-primary">Direct Solliciteren →</a>
        <a href="#over-ons" class="btn-outline">Meer Over Ons</a>
      </div>
    </div>
  </div>
</section>

<section id="over-ons">
  <div class="container">
    <div class="overons-grid">
      <div class="overons-text">
        <span class="section-label">Over {bedrijf}</span>
        <h2>{tagline.split(".")[0]} <span class="accent">{tagline.split(".")[-1].strip() if "." in tagline else ""}</span></h2>
        <p>{over}</p>
      </div>
      <div class="stats-grid">{stats_html()}</div>
    </div>
  </div>
</section>

<section id="de-functie">
  <div class="container">
    <div class="functie-header">
      <span class="section-label">Functieomschrijving</span>
      <h2>Wat ga je <span class="accent">doen?</span></h2>
    </div>
    <div class="functie-grid">
      <div class="functie-card">
        <h3>🎯 Jouw Taken</h3>
        <ul class="functie-list">{li_list(taken)}</ul>
      </div>
      <div class="functie-card">
        <h3>✅ Wat Wij Vragen</h3>
        <ul class="functie-list">{li_list(eisen)}</ul>
      </div>
    </div>
  </div>
</section>

<section id="aanbod">
  <div class="container">
    <div class="benefits-header">
      <span class="section-label">Arbeidsvoorwaarden</span>
      <h2 style="color:white">Wat wij <span style="color:var(--accent)">bieden</span></h2>
      <p class="section-sub">Bij {bedrijf} investeren we in onze mensen</p>
    </div>
    <div class="benefits-grid">{benefits_html()}</div>
  </div>
</section>

<section id="sollicitatieproces" style="background:var(--muted-bg)">
  <div class="container">
    <div style="text-align:center;margin-bottom:3.5rem">
      <span class="section-label">Hoe werkt het?</span>
      <h2>Het <span class="accent">sollicitatieproces</span></h2>
      <p class="section-sub" style="margin:0 auto;text-align:center">Transparant en snel — van sollicitatie tot jobaanbieding</p>
    </div>
    <div class="proces-steps">
      <div class="proces-line"></div>
      {proces_html()}
    </div>
    <div style="text-align:center;margin-top:3rem">
      <a href="#solliciteren" class="btn-primary">Start jouw sollicitatie →</a>
    </div>
  </div>
</section>

<section id="solliciteren">
  <div class="container">
    <span class="section-label">Interesse?</span>
    <h2>Solliciteer <span class="accent">direct</span></h2>
    <p class="section-sub">Ben jij de {functie} die wij zoeken? Word onderdeel van de {bedrijf} familie!</p>
    <div class="apply-grid">
      <div class="apply-contact">
        <h3>Neem Contact Op</h3>
        <p style="font-size:.875rem;color:var(--muted);margin-bottom:1.5rem">Stuur je CV en motivatie, of bel ons voor meer informatie.</p>
        <a href="mailto:{hr_email}" class="contact-row">
          <div class="contact-icon">✉️</div>
          <div><small>E-mail HR</small><strong>{hr_email}</strong></div>
        </a>
        {tel_html}
        <a href="{careers_url}" target="_blank" rel="noopener noreferrer" class="contact-row">
          <div class="contact-icon">🌐</div>
          <div><small>Careers</small><strong>{careers_url.replace("https://","").replace("http://","")}</strong></div>
        </a>
      </div>
      <div class="apply-cta">
        <div style="font-size:3rem;margin-bottom:1.5rem">🚀</div>
        <h4>Klaar om te starten?</h4>
        <p>Stuur je sollicitatie en we nemen snel contact met je op.</p>
        {form_html()}
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="container footer-inner">
    <div class="footer-logo"><span class="logo-accent">{logo_letter}</span>{logo_rest[1:]}<span class="logo-accent">.</span></div>
    <div class="footer-links">
      <a href="{website}" target="_blank" rel="noopener noreferrer">{website.replace("https://","").replace("http://","")}</a>
      <a href="{careers_url}" target="_blank" rel="noopener noreferrer">Careers</a>
    </div>
    <div class="footer-copy">© {year} {bedrijf}. Alle rechten voorbehouden.</div>
  </div>
</footer>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def run_pipeline(data: dict) -> dict:
    """Volledige pipeline: data → Imagen 4 → HTML → GitHub → Netlify"""
    bedrijf   = data.get("bedrijfsnaam", "bedrijf").lower().replace(" ", "-")
    functie   = data.get("functietitel", "vacature").lower().replace(" ", "-")
    sector    = data.get("sector", "default")
    timestamp = datetime.now().strftime("%Y%m")
    slug      = f"{bedrijf}-{functie}"
    gh_path   = f"pages/{slug}"

    Log.header(f"VACATUREKANON — {data.get('functietitel')} @ {data.get('bedrijfsnaam')}")
    Log.info(f"Sector: {sector} | Slug: {slug}")

    # Stap 1: Imagen 4 hero
    Log.step(1, "Hero image genereren (Imagen 4)")
    hero_bytes = generate_hero_image(sector)

    # Stap 2: Hero uploaden
    Log.step(2, "Hero image → GitHub")
    hero_path = f"{gh_path}/hero.jpg"
    github_push(hero_path, hero_bytes, f"feat: hero image {slug}")
    hero_raw_url = f"https://raw.githubusercontent.com/{CONFIG['github_repo']}/main/{hero_path}"
    Log.ok(f"Hero: {hero_raw_url}")

    # Stap 3: HTML bouwen
    Log.step(3, "HTML template bouwen")
    html = build_html(data, hero_raw_url)
    Log.ok(f"HTML: {len(html):,} tekens")

    # Stap 4: HTML uploaden
    Log.step(4, "HTML → GitHub")
    github_push(f"{gh_path}/index.html", html.encode("utf-8"),
                f"feat: landing page {slug} v{timestamp} [auto]")
    preview_url = (f"https://htmlpreview.github.io/?https://github.com/"
                   f"{CONFIG['github_repo']}/blob/main/{gh_path}/index.html")
    Log.ok(f"Preview: {preview_url}")

    # Stap 6: AI Media Pipeline (Images & Videos) genereren
    Log.step(6, "AI Media Pipeline (Kling & Leonardo) inplannen")
    Log.info("Video- en afbeeldingsgeneratie triggert op de achtergrond...")
    try:
        import subprocess
        media_script = SCRIPT_DIR.parent.parent / "scripts" / "vacaturekanon" / "vacaturekanon" / "m7-video" / "master_prompt_composer.py"
        if media_script.exists():
            subprocess.Popen([
                "python3", str(media_script),
                "--company", data.get("bedrijfsnaam", "Onbekend"),
                "--campaign-id", slug,
                "--sector", sector
            ])
            Log.ok("Media pipeline subprocess gestart")
        else:
            Log.warn("Media pipeline script niet gevonden, overgeslagen")
    except Exception as e:
        Log.warn(f"Media API Error: {e}")

    # Stap 7: Meta Ads Campagne Integratie (PAUSED)
    Log.step(7, "Meta Ads Campagne klaarzetten (Universeel)")
    Log.info("Campagne wordt opgebouwd in Meta (Status: PAUSED)")
    try:
        # Zonder hardcoded Beutech instellingen; generiek voor het IT project
        meta_script = SCRIPT_DIR.parent.parent / "scripts" / "marketing" / "meta_create_campaign.py"
        if meta_script.exists():
            subprocess.Popen([
                "python3", str(meta_script),
                "--campaign-name", f"Vacaturekanon_{slug}_{timestamp}",
                "--status", "PAUSED",
                "--url", preview_url,
                "--sector", sector
            ])
            Log.ok("Meta Campagne API script gestart (PAUSED)")
        else:
            Log.warn("Meta Api script niet gevonden in /scripts/marketing/")
    except Exception as e:
        Log.warn(f"Meta API Error: {e}")

    # Stap 8: Database (Supabase) registratie voor KPI tracking
    Log.step(8, "Supabase Database Registratie (KPI's & Analytics)")
    Log.info("Vacaturekanon campagne wordt geregistreerd in Supabase...")
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        if supabase_url and supabase_key:
            req_url = f"{supabase_url}/rest/v1/vk_campaigns"
            camp_data = {
                "campaign_id": slug,
                "company_name": data.get("bedrijfsnaam", "Onbekend"),
                "vacancy_title": data.get("functietitel", "Onbekend"),
                "sector": sector,
                "status": "PAUSED",
                "landing_page_url": preview_url,
                "webhook_url": "https://vacaturekanon.nl/.netlify/functions/meta-webhook"
            }
            req = urllib.request.Request(
                req_url, 
                data=json.dumps(camp_data).encode("utf-8"),
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                method="POST"
            )
            urllib.request.urlopen(req)
            Log.ok("Campagne succesvol in Supabase opgeslagen voor metrics.")
        else:
            Log.warn("SUPABASE_URL of _KEY ontbreekt in .env; niet in DB opgeslagen.")
    except Exception as e:
        Log.warn(f"Supabase DB error: {e}")

    # Intake opslaan
    intake_path = SCRIPT_DIR / f"intake_{slug}_{timestamp}.json"
    intake_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    result = {
        "slug": slug, "gh_path": gh_path,
        "hero_url": hero_raw_url, "preview_url": preview_url,
        "media_pipeline_triggered": True,
        "meta_campaign_status": "PAUSED",
        "supabase_registered": True,
        "generated_at": datetime.now().isoformat()
    }

    Log.header("✅ KLAAR!")
    print(f"\n  🔗 Preview: {preview_url}\n")
    return result


# ═══════════════════════════════════════════════════════════════════════════
# JOTFORM WEBHOOK SERVER
# ═══════════════════════════════════════════════════════════════════════════

def parse_vacaturetekst_with_ai(tekst: str, bedrijfsnaam: str, sector: str, hr_email: str, website: str = "") -> dict:
    """Gebruik Gemini om de volledige vacaturetekst te parsen naar gestructureerde data"""
    from google import genai

    client = genai.Client(api_key=CONFIG["gemini_api_key"])

    prompt = f"""Je bent een vacature-data extractor. Analyseer de volgende vacaturetekst en geef een JSON terug.

VACATURETEKST:
{tekst}

Geef ALLEEN geldig JSON terug (geen markdown, geen uitleg), met deze structuur:
{{
  "functietitel": "exacte functietitel uit de tekst",
  "locatie": "stad of regio",
  "dienstverband": "Fulltime of Parttime of ZZP/Freelance",
  "tagline": "wervende samenvatting in max 8 woorden",
  "over_bedrijf": "2-3 zinnen over het bedrijf uit de tekst",
  "hero_intro": "1-2 wervende zinnen voor de hero sectie",
  "taken": ["taak 1", "taak 2", "taak 3", "taak 4", "taak 5"],
  "eisen": ["eis 1", "eis 2", "eis 3", "eis 4", "eis 5"],
  "benefits": [
    {{"icon": "💰", "titel": "Korte titel", "tekst": "Korte omschrijving"}},
    {{"icon": "🚗", "titel": "Korte titel", "tekst": "Korte omschrijving"}},
    {{"icon": "📚", "titel": "Korte titel", "tekst": "Korte omschrijving"}},
    {{"icon": "🛡️", "titel": "Korte titel", "tekst": "Korte omschrijving"}}
  ],
  "stats": [
    {{"waarde": "getal of tekst", "label": "label"}},
    {{"waarde": "getal of tekst", "label": "label"}}
  ],
  "hr_telefoon": "telefoonnummer als gevonden anders leeg",
  "opgericht": "jaar als gevonden anders leeg",
  "medewerkers": "aantal medewerkers als gevonden anders leeg"
}}

Gebruik alleen informatie die in de tekst staat. Verzin niets."""

    print("  🤖 Gemini parseert vacaturetekst...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    raw = response.text.strip()
    # Verwijder markdown code blocks als aanwezig
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    parsed = json.loads(raw)
    print(f"  ✅ Geparseerd: {parsed.get('functietitel')} | {parsed.get('locatie')}")

    # Basis velden toevoegen
    parsed["bedrijfsnaam"]  = bedrijfsnaam
    parsed["sector"]        = sector
    parsed["hr_email"]      = hr_email
    parsed["website"]       = website or parsed.get("website", "#")
    parsed["careers_url"]   = parsed.get("careers_url", f"{website}/careers" if website else "#")
    parsed["accent_kleur"]  = SECTOR_COLORS.get(sector, "#f97316")

    return parsed


def parse_jotform(raw: str) -> dict:
    """Parse Jotform POST data — slim 5-velden formulier met AI parsing"""
    fields = urllib.parse.parse_qs(raw, keep_blank_values=True)
    flat   = {k: urllib.parse.unquote_plus(v[0]).strip() for k, v in fields.items() if v}

    # Nieuw slim formulier (5 velden)
    bedrijfsnaam   = flat.get("q1_bedrijfsnaam", flat.get("q3_bedrijfsnaam", "Onbekend"))
    sector         = flat.get("q2_sector",        flat.get("q8_sector",       "default"))
    hr_email       = flat.get("q3_hrEmail",        flat.get("q21_hrEmail",    ""))
    vacaturetekst  = flat.get("q4_vacaturetekst",  "")
    website        = flat.get("q5_website",         flat.get("q7_website",    ""))

    if vacaturetekst and len(vacaturetekst) > 50:
        # Slim: AI parset de volledige vacaturetekst
        return parse_vacaturetekst_with_ai(vacaturetekst, bedrijfsnaam, sector, hr_email, website)
    else:
        # Fallback: oud uitgebreid formulier
        Log.warn("Geen vacaturetekst gevonden — gebruik oud veldformaat")
        data = {"bedrijfsnaam": bedrijfsnaam, "sector": sector, "hr_email": hr_email,
                "website": website, "accent_kleur": SECTOR_COLORS.get(sector, "#f97316")}
        for k, v in flat.items():
            if k not in data:
                data[k] = v
        return data


class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")

    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Vacaturekanon Webhook Server v2 - POST /webhook")

    def do_POST(self):
        if self.path not in ("/webhook", "/webhook/"):
            self.send_response(404); self.end_headers(); return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        print(f"\n[WEBHOOK] Ontvangen ({len(body)} bytes)")

        try:
            data = parse_jotform(body)
            Log.info(f"Bedrijf: {data.get('bedrijfsnaam','?')} | Functie: {data.get('functietitel','?')}")

            # Genereer async zodat webhook snel reageert
            t = threading.Thread(target=run_pipeline, args=(data,), daemon=True)
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "accepted",
                "message": f"Pagina wordt gegenereerd voor {data.get('bedrijfsnaam')} - {data.get('functietitel')}",
            }).encode())
        except Exception as e:
            Log.err(str(e))
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


# ═══════════════════════════════════════════════════════════════════════════
# SETUP RAPPORT
# ═══════════════════════════════════════════════════════════════════════════

def run_setup():
    """Print volledig systeem overzicht"""
    Log.header("VACATUREKANON v2 — SYSTEEM SETUP")

    # Omgeving checken
    Log.header("OMGEVING")
    checks = {
        "GEMINI_API_KEY":  CONFIG["gemini_api_key"][:12] + "..." if CONFIG["gemini_api_key"] else "",
        "GITHUB_TOKEN":    CONFIG["github_token"][:12] + "..." if CONFIG["github_token"] else "",
        "GITHUB_REPO":     CONFIG["github_repo"],
        "NETLIFY_HOOK_URL":CONFIG["netlify_hook"] or "niet ingesteld",
        "IMAGEN_MODEL":    CONFIG["imagen_model"],
    }
    for k, v in checks.items():
        sym = "✅" if v and "niet" not in v else "⚠️ "
        print(f"  {sym} {k}: {v}")

    # MCP servers
    Log.header("MCP SERVERS")
    for name, url in MCP_SERVERS:
        print(f"  ✅ {name}: {url[:50]}...")

    # Jotform schema
    Log.header("JOTFORM VELDEN")
    total = 0
    for sectie, fields in JOTFORM_FIELDS.items():
        req = sum(1 for _, _, r in fields.values() if r)
        print(f"  📋 {sectie}: {len(fields)} velden ({req} verplicht)")
        total += len(fields)
    print(f"\n  Totaal: {total} velden")

    # Email sequences
    Log.header("EMAIL SEQUENCES")
    for key, seq in EMAIL_SEQUENCES.items():
        print(f"  ✅ {seq['name']} ({seq['trigger']})")

    # Sectoren
    Log.header("SECTOR PROMPTS")
    for sector in SECTOR_PROMPTS:
        color = SECTOR_COLORS.get(sector, "#f97316")
        print(f"  🎨 {sector}: {color}")

    Log.header("VOLGENDE STAPPEN")
    print("""  1. Maak Jotform aan: https://www.jotform.com
  2. Voeg velden toe (zie JOTFORM_FIELDS hierboven)
  3. Stel webhook in: Settings → Integrations → Webhooks
     URL: http://JOUW-IP:5055/webhook
  4. Start webhook server: python3 vacaturekanon_v2.py --webhook
  5. Test: python3 vacaturekanon_v2.py --test
""")


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vacaturekanon Orchestrator v2")
    parser.add_argument("--setup",    action="store_true", help="Systeem overzicht tonen")
    parser.add_argument("--webhook",  action="store_true", help="Webhook server starten")
    parser.add_argument("--generate", metavar="FILE",      help="Genereer van JSON bestand")
    parser.add_argument("--test",     action="store_true", help="Test met J de Jonge demo data")
    args = parser.parse_args()

    if args.setup:
        run_setup()

    elif args.webhook:
        port = CONFIG["webhook_port"]
        print(f"""
╔══════════════════════════════════════════════╗
║  VACATUREKANON Webhook Server v2             ║
║  Poort: {port}                                  ║
║  URL:   http://0.0.0.0:{port}/webhook         ║
║  Ctrl+C om te stoppen                        ║
╚══════════════════════════════════════════════╝""")
        HTTPServer(("0.0.0.0", port), WebhookHandler).serve_forever()

    elif args.generate:
        with open(args.generate, encoding="utf-8") as f:
            data = json.load(f)
        result = run_pipeline(data)
        print(json.dumps(result, indent=2))

    elif args.test:
        print("🧪 Test mode — J de Jonge Voorman")
        demo = {
            "bedrijfsnaam": "J de Jonge", "bedrijfsnaam_kort": "J",
            "tagline": "Creating The Next-Gen Industry",
            "over_bedrijf": "Sinds 1954 is J de Jonge een vertrouwde leider in EPC-contractering.\nGespecialiseerd in mechanische en piping systemen.\nMet locaties in Nederland, België, Duitsland en Saudi-Arabië.",
            "website": "https://jdejonge.com", "sector": "constructie",
            "opgericht": "1954", "medewerkers": "217+",
            "stats": [{"waarde":"16.844m²","label":"Productiecapaciteit"},{"waarde":"217+","label":"Medewerkers"},{"waarde":"1954","label":"Opgericht"},{"waarde":"55+","label":"Culturen"}],
            "functietitel": "Voorman", "locatie": "Nederland", "dienstverband": "Fulltime",
            "hero_intro": "Join The Next Gen Connectors. Word onderdeel van een familiebedrijf waar innovatie en samenwerking de toekomst van engineering vormgeven.",
            "taken": ["Aansturen en coördineren van montage- en constructieploegen","Toezicht houden op kwaliteit en voortgang van projecten","Werkplanningen opstellen en bewaken","Communiceren met projectmanagers en opdrachtgevers","Zorgen voor veilige werkomgeving (VCA)"],
            "eisen": ["Minimaal 5 jaar ervaring in de industriële of EPC-sector","Relevante technische opleiding (MBO/HBO)","VCA-VOL certificaat","Ervaring met mechanische installaties en piping","Rijbewijs B"],
            "benefits": [{"icon":"💰","titel":"Competitief Salaris","tekst":"Marktconform salaris passend bij ervaring"},{"icon":"🚗","titel":"Bedrijfsauto","tekst":"Volledige bedrijfsauto inclusief privégebruik"},{"icon":"📚","titel":"Flow Academy","tekst":"Groei via onze eigen Flow Academy"},{"icon":"🛡️","titel":"Pensioen","tekst":"Uitstekende pensioenregeling"},{"icon":"🤝","titel":"Team","tekst":"Hechte no-nonsense familie cultuur"},{"icon":"🌍","titel":"Internationaal","tekst":"Projecten in NL, Europa en worldwide"},{"icon":"⚡","titel":"Innovatie","tekst":"Cutting-edge technologie en systemen"},{"icon":"🌱","titel":"Duurzaam","tekst":"CO₂ Prestatieladder niveau 3"}],
            "hr_email": "hr@jdejonge.com", "hr_telefoon": "+31 (0)10 248 58 00",
            "careers_url": "https://jdejonge.com/careers",
        }
        result = run_pipeline(demo)
        print(json.dumps(result, indent=2))

    else:
        parser.print_help()
