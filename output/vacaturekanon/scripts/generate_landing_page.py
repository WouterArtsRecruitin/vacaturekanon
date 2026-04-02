#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   VACATUREKANON — Landing Page Generator v2.0                       ║
║   Recruitin B.V. | Wouter Arts                                      ║
║                                                                     ║
║   Pipeline: Jotform JSON → Hero Image (Imagen 4) → HTML → GitHub   ║
╚══════════════════════════════════════════════════════════════════════╝

Gebruik:
    python3 generate_landing_page.py --input vacature.json
    python3 generate_landing_page.py --jotform-id 12345678

Configuratie via .env of environment variables:
    GEMINI_API_KEY      → Google Imagen 4 (betaald plan)
    GITHUB_TOKEN        → GitHub push
    GITHUB_REPO         → WouterArtsRecruitin/vacaturekanon-landing-pages
    NETLIFY_HOOK_URL    → Netlify deploy webhook (optioneel)
    IMAGE_ENGINE        → "imagen4" | "pollinations" (default: pollinations)
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
GITHUB_TOKEN     = os.getenv("GITHUB_TOKEN", "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")
GITHUB_REPO      = os.getenv("GITHUB_REPO", "WouterArtsRecruitin/vacaturekanon-landing-pages")
NETLIFY_HOOK_URL = os.getenv("NETLIFY_HOOK_URL", "")
IMAGE_ENGINE     = os.getenv("IMAGE_ENGINE", "pollinations")  # "imagen4" of "pollinations"

# ═══════════════════════════════════════════════════════════════════════
# SECTOR → IMAGE PROMPT LIBRARY
# ═══════════════════════════════════════════════════════════════════════
SECTOR_PROMPTS = {
    "constructie": {
        "hero": (
            "Cinematic professional recruitment photography. Dutch male construction foreman, "
            "early 40s, dark brown hair neatly combed, light beard, strong jawline, "
            "wearing dark navy work jacket and orange high-vis vest, yellow hard hat. "
            "Standing confidently on a large industrial construction site at golden hour. "
            "Steel beams, cranes, scaffolding in background bokeh. "
            "85mm lens, shallow depth of field, dramatic warm lighting. "
            "No text, no watermarks, no logos. Photorealistic."
        ),
        "about": (
            "Professional team of Dutch construction engineers reviewing blueprints "
            "on an active construction site. Overcast sky, natural lighting. "
            "Hard hats and high-vis gear. No text."
        )
    },
    "oil_gas": {
        "hero": (
            "Cinematic professional recruitment photography. Dutch male EPC engineer, "
            "early 40s, dark hair, light beard, wearing orange high-vis jacket and "
            "safety glasses. Standing confidently on large industrial oil refinery "
            "with pipes and tanks, golden hour lighting. "
            "85mm lens, bokeh background. No text, no watermarks. Photorealistic."
        ),
        "about": (
            "Industrial oil and gas refinery at sunset, large chemical tanks and "
            "pipe systems. Professional engineering environment. "
            "Dutch landscape. No text."
        )
    },
    "productie": {
        "hero": (
            "Cinematic professional recruitment photography. Dutch male production manager, "
            "early 40s, confident smile, wearing company polo shirt and safety equipment. "
            "Modern factory production floor, assembly lines, machinery in background bokeh. "
            "85mm lens, professional lighting. No text, no watermarks. Photorealistic."
        ),
        "about": (
            "Modern Dutch manufacturing facility, clean production environment, "
            "CNC machines and robotic arms. Professional industrial setting. No text."
        )
    },
    "automation": {
        "hero": (
            "Cinematic professional recruitment photography. Dutch male automation engineer, "
            "early 40s, dark hair, light stubble, wearing neat dark work wear. "
            "Control room or automation panel with screens and equipment. "
            "Professional confident pose. 85mm lens, bokeh. No text. Photorealistic."
        ),
        "about": (
            "Modern industrial automation control room, multiple screens showing "
            "process data, Dutch engineer at work. Professional setting. No text."
        )
    },
    "renewable": {
        "hero": (
            "Cinematic professional recruitment photography. Dutch male renewable energy "
            "technician, early 40s, dark hair, wearing wind energy work gear and "
            "safety harness. Wind turbines in background at golden hour. "
            "Dutch landscape, dramatic sky. 85mm lens, bokeh. No text. Photorealistic."
        ),
        "about": (
            "Dutch offshore wind farm at golden hour, wind turbines on North Sea. "
            "Aerial perspective, dramatic clouds. No text."
        )
    },
    "default": {
        "hero": (
            "Cinematic professional recruitment photography. Dutch male skilled worker, "
            "early 40s, dark hair neatly groomed, light beard, wearing professional "
            "work attire appropriate for industrial sector. Confident pose at worksite. "
            "85mm lens, bokeh background, golden hour lighting. No text. Photorealistic."
        ),
        "about": (
            "Professional Dutch industrial work environment, clean and modern. "
            "Workers in background. Natural lighting. No text."
        )
    }
}

# ═══════════════════════════════════════════════════════════════════════
# IMAGE GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_image_pollinations(prompt: str, width: int = 1344, height: int = 768) -> bytes:
    """Gratis image generation via Pollinations.ai (FLUX Pro model) met retry"""
    import time, random

    # Gebruik kortere prompt voor betrouwbaarheid
    short_prompt = prompt[:300]
    encoded = urllib.parse.quote(short_prompt)
    seed = abs(hash(prompt)) % 99999

    # Probeer flux-pro, fallback naar flux
    for model in ["flux-pro", "flux"]:
        url = (f"https://image.pollinations.ai/prompt/{encoded}"
               f"?width={width}&height={height}&model={model}&nologo=true&seed={seed}&enhance=true")
        print(f"  🎨 Generating image via Pollinations.ai (model={model})...")

        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "VacatureKanon/2.0"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    data = r.read()
                    if len(data) > 5000:  # geldig image (>5KB)
                        print(f"  ✅ Image genereerd: {len(data):,} bytes")
                        return data
            except Exception as e:
                print(f"  ⚠️  Poging {attempt+1}/3 mislukt: {e}")
                if attempt < 2:
                    time.sleep(random.uniform(3, 7))

    raise RuntimeError("Pollinations.ai niet beschikbaar na 3 pogingen")


def generate_image_imagen4(prompt: str) -> bytes:
    """Premium image generation via Google Imagen 4 (betaald plan vereist)"""
    try:
        from google import genai
        from google.genai import types

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY niet ingesteld")

        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"  🎨 Generating image via Google Imagen 4...")
        response = client.models.generate_images(
            model="imagen-4.0-fast-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9"
            )
        )
        return response.generated_images[0].image.image_bytes
    except ImportError:
        raise ImportError("google-genai niet geïnstalleerd: pip install google-genai")


def generate_image(prompt: str, engine: str = None) -> bytes:
    """Genereer een image met de geconfigureerde engine"""
    engine = engine or IMAGE_ENGINE
    if engine == "imagen4":
        return generate_image_imagen4(prompt)
    else:
        return generate_image_pollinations(prompt)


# ═══════════════════════════════════════════════════════════════════════
# GITHUB UPLOAD
# ═══════════════════════════════════════════════════════════════════════

def github_get_sha(path: str) -> str | None:
    """Haal SHA op van bestaand bestand (nodig voor update)"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r).get("sha")
    except urllib.error.HTTPError:
        return None


def github_push(path: str, content: bytes, message: str) -> str:
    """Push bestand naar GitHub, return download URL"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    sha = github_get_sha(path)

    payload = {
        "message": message,
        "content": base64.b64encode(content).decode()
    }
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PUT", headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    })

    with urllib.request.urlopen(req) as r:
        result = json.load(r)
        return result["content"]["download_url"]


# ═══════════════════════════════════════════════════════════════════════
# HTML TEMPLATE BUILDER
# ═══════════════════════════════════════════════════════════════════════

def build_html(data: dict, hero_url: str) -> str:
    """Vul het HTML template in met Jotform data"""

    # Bedrijfsgegevens
    bedrijf       = data.get("bedrijfsnaam", "Bedrijfsnaam")
    bedrijf_kort  = data.get("bedrijfsnaam_kort", bedrijf[:1])  # eerste letter voor logo-accent
    tagline       = data.get("tagline", "Wij bouwen aan de toekomst")
    over_bedrijf  = data.get("over_bedrijf", "Een toonaangevend bedrijf in de sector.")
    website       = data.get("website", "#")
    sector        = data.get("sector", "constructie")
    opgericht     = data.get("opgericht", "")
    medewerkers   = data.get("medewerkers", "")
    locaties      = data.get("locaties", "Nederland")

    # Vacature
    functie       = data.get("functietitel", "Vacature")
    functie_short = data.get("functietitel_kort", functietitel_to_short(functie))
    locatie_vac   = data.get("locatie", "Nederland")
    dienstverband = data.get("dienstverband", "Fulltime")
    intro_tekst   = data.get("hero_intro", f"Word onderdeel van {bedrijf} en draag bij aan uitdagende projecten in de sector.")

    # Taken & eisen
    taken         = data.get("taken", ["Aansturen van projectteams", "Kwaliteitscontrole"])
    eisen         = data.get("eisen", ["Relevante werkervaring", "Communicatief sterk"])

    # Benefits
    benefits      = data.get("benefits", [
        {"titel": "Competitief Salaris", "tekst": "Marktconform salaris passend bij je ervaring"},
        {"titel": "Groei", "tekst": "Ruimte voor persoonlijke en professionele ontwikkeling"},
        {"titel": "Team", "tekst": "Hecht team met open cultuur"},
        {"titel": "Zekerheid", "tekst": "Vast contract bij goed functioneren"}
    ])

    # Sollicitatie
    hr_email      = data.get("hr_email", f"hr@{website.replace('https://','').replace('http://','').split('/')[0]}")
    hr_telefoon   = data.get("hr_telefoon", "")
    careers_url   = data.get("careers_url", f"{website}/careers")

    # Kleuren (optioneel overschrijven)
    accent_color  = data.get("accent_kleur", "#f97316")  # default oranje
    hero_dark     = data.get("hero_dark", "#0f172a")

    # Statistieken
    stats = data.get("stats", [])
    if opgericht and not any(s.get("label") == "Opgericht" for s in stats):
        stats.append({"waarde": str(opgericht), "label": "Opgericht"})
    if medewerkers and not any(s.get("label") == "Medewerkers" for s in stats):
        stats.append({"waarde": str(medewerkers), "label": "Medewerkers"})

    # Proces stappen
    proces = data.get("sollicitatieproces", [
        {"nr": "1", "titel": "Solliciteer", "tekst": f"Stuur je CV en motivatie naar {hr_email}", "tijd": "~1 dag"},
        {"nr": "2", "titel": "Kennismaking", "tekst": "Telefonisch gesprek (±15 min) met onze recruiter", "tijd": "~3 dagen"},
        {"nr": "3", "titel": "Gesprek", "tekst": "Face-to-face gesprek op locatie + kennismaking met het team", "tijd": "~1 week"},
        {"nr": "4", "titel": "Jobaanbieding", "tekst": f"Welkom bij {bedrijf}! Onboarding en start", "tijd": "~2-3 weken"}
    ])

    # Genereer HTML
    taken_html    = "\n".join([f'<li>{taak}</li>' for taak in taken])
    eisen_html    = "\n".join([f'<li>{eis}</li>' for eis in eisen])
    benefits_html = build_benefits_html(benefits)
    stats_html    = build_stats_html(stats)
    proces_html   = build_proces_html(proces)

    # Jotform embed of mailto
    jotform_id    = data.get("jotform_id", "")
    form_html     = build_form_html(jotform_id, hr_email, functie, bedrijf)

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{functie} Vacature | {bedrijf}</title>
  <meta name="description" content="{bedrijf} zoekt een {functie}. {intro_tekst[:120]}">
  <meta property="og:title" content="{functie} | {bedrijf}">
  <meta property="og:description" content="{intro_tekst[:200]}">
  <meta property="og:image" content="{hero_url}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #FFFFFF; --fg: #0f172a; --muted: #64748b; --muted-bg: #f8fafc;
      --accent: {accent_color}; --accent-dk: {darken(accent_color)};
      --hero-bg: {hero_dark}; --border: #e2e8f0; --radius: 12px;
    }}
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--fg); }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
    /* HEADER */
    header {{ position: fixed; top: 0; left: 0; right: 0; z-index: 50;
      background: rgba(15,23,42,0.95); backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.08); }}
    .header-inner {{ display: flex; align-items: center; justify-content: space-between; height: 72px; }}
    .logo {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.25rem; color: white; text-decoration: none; }}
    .logo-accent {{ color: var(--accent); }}
    .nav-links {{ display: flex; align-items: center; gap: 2rem; list-style: none; }}
    .nav-links a {{ font-size: 0.875rem; font-weight: 500; color: rgba(255,255,255,0.7); text-decoration: none; transition: color 0.2s; }}
    .nav-links a:hover {{ color: white; }}
    .btn-nav {{ background: var(--accent); color: white; padding: 10px 20px; border-radius: 8px;
      font-size: 0.875rem; font-weight: 600; text-decoration: none; transition: background 0.2s; }}
    .btn-nav:hover {{ background: var(--accent-dk); }}
    /* HERO */
    #hero {{ position: relative; min-height: 100vh; display: flex; align-items: center; overflow: hidden; }}
    .hero-bg {{ position: absolute; inset: 0; }}
    .hero-bg img {{ width: 100%; height: 100%; object-fit: cover; object-position: center top; }}
    .hero-bg-overlay {{ position: absolute; inset: 0; background: linear-gradient(135deg,rgba(10,18,35,0.85) 0%,rgba(15,30,55,0.6) 60%,rgba(10,18,35,0.45) 100%); }}
    .hero-fade {{ position: absolute; bottom: 0; left: 0; right: 0; height: 120px; background: linear-gradient(to top,var(--bg),transparent); z-index: 2; }}
    .hero-content {{ position: relative; z-index: 3; padding: 9rem 0 6rem; max-width: 780px; }}
    .hero-badge {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 100px; background: rgba(249,115,22,0.15); backdrop-filter: blur(4px); margin-bottom: 1.5rem; }}
    .hero-badge .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }}
    .hero-badge span {{ font-size: 0.875rem; font-weight: 500; color: white; }}
    h1 {{ font-family: 'Space Grotesk', sans-serif; font-size: clamp(3rem,7vw,5rem); font-weight: 700; line-height: 1.05; color: white; margin-bottom: 1.5rem; letter-spacing: -1px; }}
    .hero-sub {{ font-size: 1.2rem; color: rgba(255,255,255,0.75); line-height: 1.7; margin-bottom: 2rem; max-width: 580px; }}
    .hero-location {{ display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,0.6); font-size: 0.9rem; margin-bottom: 2.5rem; }}
    .hero-ctas {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
    .btn-primary {{ display: inline-flex; align-items: center; gap: 8px; background: var(--accent); color: white; padding: 14px 28px; border-radius: 8px; font-size: 1rem; font-weight: 600; text-decoration: none; transition: background 0.2s, transform 0.15s; box-shadow: 0 4px 16px rgba(249,115,22,0.4); }}
    .btn-primary:hover {{ background: var(--accent-dk); transform: translateY(-1px); }}
    .btn-outline {{ display: inline-flex; align-items: center; gap: 8px; border: 1.5px solid rgba(255,255,255,0.3); color: white; padding: 14px 28px; border-radius: 8px; font-size: 1rem; font-weight: 500; text-decoration: none; background: transparent; transition: border-color 0.2s, background 0.2s; }}
    .btn-outline:hover {{ border-color: rgba(255,255,255,0.7); background: rgba(255,255,255,0.08); }}
    /* SECTIONS */
    section {{ padding: 6rem 0; }}
    .section-label {{ display: block; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent); margin-bottom: 1rem; }}
    h2 {{ font-family: 'Space Grotesk', sans-serif; font-size: clamp(2rem,4vw,3rem); font-weight: 700; color: var(--fg); line-height: 1.15; letter-spacing: -0.5px; margin-bottom: 1.25rem; }}
    h2 .accent {{ color: var(--accent); }}
    .section-sub {{ font-size: 1.05rem; color: var(--muted); line-height: 1.75; max-width: 600px; }}
    /* OVER ONS */
    .overons-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: start; margin-top: 3.5rem; }}
    .overons-text p {{ font-size: 0.95rem; line-height: 1.8; color: #475569; margin-bottom: 1.25rem; }}
    .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    .stat-card {{ background: var(--muted-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; }}
    .stat-icon {{ width: 40px; height: 40px; border-radius: 8px; background: rgba(249,115,22,0.1); display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; }}
    .stat-num {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.75rem; font-weight: 700; color: var(--fg); }}
    .stat-label {{ font-size: 0.8rem; color: var(--muted); margin-top: 2px; }}
    /* FUNCTIE */
    #de-functie {{ background: var(--muted-bg); }}
    .functie-header {{ text-align: center; margin-bottom: 3rem; }}
    .functie-header .section-sub {{ margin: 0 auto; text-align: center; }}
    .functie-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }}
    .functie-card {{ background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 2rem; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }}
    .functie-card h3 {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: var(--fg); margin-bottom: 1.5rem; }}
    .functie-list {{ list-style: none; }}
    .functie-list li {{ display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 0.9rem; line-height: 1.6; color: #475569; }}
    .functie-list li:last-child {{ border-bottom: none; }}
    .functie-list li::before {{ content: "✓"; color: var(--accent); font-weight: 700; flex-shrink: 0; margin-top: 1px; }}
    /* BENEFITS */
    #aanbod {{ background: var(--hero-bg); }}
    #aanbod h2 {{ color: white; }}
    #aanbod .section-label {{ color: rgba(249,115,22,0.85); }}
    #aanbod .section-sub {{ color: rgba(255,255,255,0.55); }}
    .benefits-header {{ text-align: center; margin-bottom: 3rem; }}
    .benefits-header .section-sub {{ margin: 0 auto; text-align: center; }}
    .benefits-grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; }}
    .benefit-card {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius); padding: 1.5rem; transition: background 0.2s, transform 0.2s; }}
    .benefit-card:hover {{ background: rgba(249,115,22,0.08); border-color: rgba(249,115,22,0.25); transform: translateY(-3px); }}
    .benefit-card h4 {{ font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; font-weight: 700; color: white; margin-bottom: 0.4rem; }}
    .benefit-card p {{ font-size: 0.82rem; color: rgba(255,255,255,0.45); line-height: 1.6; }}
    .benefit-icon {{ font-size: 1.5rem; margin-bottom: 0.75rem; }}
    /* PROCES */
    #sollicitatieproces {{ background: var(--muted-bg); }}
    .proces-steps {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 0; position: relative; margin-top: 3rem; }}
    .proces-line {{ position: absolute; top: 28px; left: 12.5%; right: 12.5%; height: 2px; background: linear-gradient(to right,var(--accent),rgba(249,115,22,0.3)); z-index: 0; }}
    .proces-step {{ text-align: center; padding: 0 1rem; position: relative; z-index: 1; }}
    .proces-nr {{ width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.2rem; }}
    .proces-nr.active {{ background: var(--accent); color: white; box-shadow: 0 4px 16px rgba(249,115,22,0.4); }}
    .proces-nr.inactive {{ background: white; border: 2px solid var(--accent); color: var(--accent); }}
    .proces-step h4 {{ font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 700; color: var(--fg); margin-bottom: 0.5rem; }}
    .proces-step p {{ font-size: 0.83rem; color: var(--muted); line-height: 1.6; }}
    .proces-step .tijd {{ margin-top: 0.75rem; font-size: 0.72rem; color: var(--accent); font-weight: 600; }}
    /* SOLLICITEREN */
    .apply-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 3rem; }}
    .apply-contact {{ background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 2rem; }}
    .apply-contact h3 {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 700; color: var(--fg); margin-bottom: 1.5rem; }}
    .contact-row {{ display: flex; align-items: center; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid var(--border); text-decoration: none; color: var(--fg); transition: color 0.2s; }}
    .contact-row:last-child {{ border-bottom: none; }}
    .contact-row:hover {{ color: var(--accent); }}
    .contact-icon {{ width: 44px; height: 44px; border-radius: 10px; background: rgba(249,115,22,0.1); flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }}
    .contact-row small {{ display: block; font-size: 0.72rem; color: var(--muted); }}
    .contact-row strong {{ font-weight: 600; font-size: 0.9rem; }}
    .apply-cta {{ background: var(--hero-bg); border-radius: var(--radius); padding: 2.5rem; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
    .apply-cta h4 {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: white; margin-bottom: 0.75rem; }}
    .apply-cta p {{ font-size: 0.9rem; color: rgba(255,255,255,0.6); line-height: 1.7; margin-bottom: 2rem; }}
    .apply-cta .btn-primary {{ width: 100%; justify-content: center; }}
    /* FOOTER */
    footer {{ background: var(--hero-bg); color: white; padding: 3rem 0; border-top: 1px solid rgba(255,255,255,0.06); }}
    .footer-inner {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1.5rem; }}
    .footer-logo {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.1rem; color: white; }}
    .footer-links {{ display: flex; gap: 1.5rem; }}
    .footer-links a {{ font-size: 0.82rem; color: rgba(255,255,255,0.55); text-decoration: none; transition: color 0.2s; }}
    .footer-links a:hover {{ color: var(--accent); }}
    .footer-copy {{ font-size: 0.8rem; color: rgba(255,255,255,0.4); }}
    /* RESPONSIVE */
    @media (max-width: 900px) {{
      .overons-grid, .functie-grid, .apply-grid {{ grid-template-columns: 1fr; }}
      .benefits-grid, .proces-steps {{ grid-template-columns: 1fr 1fr; }}
      .nav-links {{ display: none; }}
    }}
  </style>
</head>
<body>
<header>
  <div class="container header-inner">
    <a href="#" class="logo"><span class="logo-accent">{bedrijf_kort[0].upper()}</span>{bedrijf[len(bedrijf_kort[0]):]}<span class="logo-accent">.</span></a>
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
      <h1>{functie}<br><span style="color:var(--accent)">{bedrijf[:1]}</span>{bedrijf[1:]}<span style="color:var(--accent)">.</span></h1>
      <p class="hero-sub">{intro_tekst}</p>
      <div class="hero-location">📍 {locatie_vac} &bull; {dienstverband}</div>
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
        <h2>{tagline.split('.')[0]} <span class="accent">{tagline.split('.')[-1].strip() if '.' in tagline else ''}</span></h2>
        {''.join(f'<p>{p.strip()}</p>' for p in over_bedrijf.split('\\n') if p.strip())}
      </div>
      <div class="stats-grid">{stats_html}</div>
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
        <ul class="functie-list">{taken_html}</ul>
      </div>
      <div class="functie-card">
        <h3>✅ Wat Wij Vragen</h3>
        <ul class="functie-list">{eisen_html}</ul>
      </div>
    </div>
  </div>
</section>

<section id="aanbod">
  <div class="container">
    <div class="benefits-header">
      <span class="section-label">Arbeidsvoorwaarden</span>
      <h2>Wat wij <span style="color:var(--accent)">bieden</span></h2>
      <p class="section-sub">Bij {bedrijf} investeren we in onze medewerkers</p>
    </div>
    <div class="benefits-grid">{benefits_html}</div>
  </div>
</section>

<section id="sollicitatieproces">
  <div class="container">
    <div style="text-align:center;margin-bottom:3.5rem;">
      <span class="section-label">Hoe werkt het?</span>
      <h2>Het <span class="accent">sollicitatieproces</span></h2>
      <p class="section-sub" style="margin:0 auto;text-align:center;">Transparant en snel — van sollicitatie tot jobaanbieding</p>
    </div>
    <div class="proces-steps">
      <div class="proces-line"></div>
      {proces_html}
    </div>
    <div style="text-align:center;margin-top:3rem;">
      <a href="#solliciteren" class="btn-primary">Start jouw sollicitatie →</a>
    </div>
  </div>
</section>

<section id="solliciteren">
  <div class="container">
    <span class="section-label">Interesse?</span>
    <h2>Solliciteer <span class="accent">direct</span></h2>
    <p class="section-sub">Ben jij de {functie_short} die wij zoeken? Word onderdeel van de {bedrijf} familie!</p>
    <div class="apply-grid">
      <div class="apply-contact">
        <h3>Neem Contact Op</h3>
        <p style="font-size:.875rem;color:var(--muted);margin-bottom:1.5rem;">Stuur je CV en motivatie, of bel ons voor meer informatie.</p>
        <a href="mailto:{hr_email}" class="contact-row">
          <div class="contact-icon">✉️</div>
          <div><small>E-mail HR</small><strong>{hr_email}</strong></div>
        </a>
        {'<a href="tel:' + hr_telefoon.replace(' ','') + '" class="contact-row"><div class="contact-icon">📞</div><div><small>Telefoon</small><strong>' + hr_telefoon + '</strong></div></a>' if hr_telefoon else ''}
        <a href="{careers_url}" target="_blank" rel="noopener noreferrer" class="contact-row">
          <div class="contact-icon">🌐</div>
          <div><small>Careers Pagina</small><strong>{careers_url.replace('https://','')}</strong></div>
        </a>
      </div>
      <div class="apply-cta">
        <div style="font-size:3rem;margin-bottom:1.5rem;">🚀</div>
        <h4>Klaar om te starten?</h4>
        <p>Stuur je sollicitatie en we nemen snel contact met je op.</p>
        {form_html}
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="container footer-inner">
    <div class="footer-logo"><span style="color:var(--accent)">{bedrijf[:1]}</span>{bedrijf[1:]}<span style="color:var(--accent)">.</span></div>
    <div class="footer-links">
      <a href="{website}" target="_blank" rel="noopener noreferrer">{website.replace('https://','').replace('http://','')}</a>
      <a href="{careers_url}" target="_blank" rel="noopener noreferrer">Careers</a>
    </div>
    <div class="footer-copy">© {datetime.now().year} {bedrijf}. Alle rechten voorbehouden.</div>
  </div>
</footer>
</body>
</html>"""


# ── HELPER FUNCTIONS ─────────────────────────────────────────────────

def darken(hex_color: str) -> str:
    """Maak kleur 10% donkerder"""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = max(0, int(r * 0.88)), max(0, int(g * 0.88)), max(0, int(b * 0.88))
    return f"#{r:02x}{g:02x}{b:02x}"


def functietitel_to_short(titel: str) -> str:
    """Verkort functietitel bijv 'Senior Projectmanager' → 'projectmanager'"""
    words = titel.lower().split()
    return words[-1] if words else titel.lower()


def build_stats_html(stats: list) -> str:
    icons = ["🏭", "👥", "🏆", "🌍", "📅", "⭐"]
    html = ""
    for i, stat in enumerate(stats[:4]):
        icon = icons[i % len(icons)]
        html += f"""<div class="stat-card">
      <div class="stat-icon">{icon}</div>
      <div class="stat-num">{stat.get('waarde', '')}</div>
      <div class="stat-label">{stat.get('label', '')}</div>
    </div>\n"""
    return html


def build_benefits_html(benefits: list) -> str:
    benefit_icons = ["💰", "🚗", "📚", "🛡️", "🤝", "🌍", "⚡", "🌱", "💪", "🎯"]
    html = ""
    for i, b in enumerate(benefits[:8]):
        icon = b.get("icon", benefit_icons[i % len(benefit_icons)])
        html += f"""<div class="benefit-card">
      <div class="benefit-icon">{icon}</div>
      <h4>{b.get('titel', '')}</h4>
      <p>{b.get('tekst', '')}</p>
    </div>\n"""
    return html


def build_proces_html(proces: list) -> str:
    html = ""
    for i, stap in enumerate(proces):
        nr_class = "active" if i == 0 else "inactive"
        html += f"""<div class="proces-step">
      <div class="proces-nr {nr_class}">{stap.get('nr', i+1)}</div>
      <h4>{stap.get('titel', '')}</h4>
      <p>{stap.get('tekst', '')}</p>
      <div class="tijd">{stap.get('tijd', '')}</div>
    </div>\n"""
    return html


def build_form_html(jotform_id: str, hr_email: str, functie: str, bedrijf: str) -> str:
    if jotform_id:
        return f"""<a href="https://form.jotform.com/{jotform_id}" target="_blank" rel="noopener noreferrer" class="btn-primary" style="width:100%;justify-content:center;">✉️ Solliciteer Nu</a>
      <p style="font-size:0.75rem;color:rgba(255,255,255,0.4);margin-top:1rem;">Veilig via Jotform</p>"""
    else:
        subject = urllib.parse.quote(f"Sollicitatie {functie} - {bedrijf}")
        return f"""<a href="mailto:{hr_email}?subject={subject}" class="btn-primary" style="width:100%;justify-content:center;">✉️ Solliciteer Nu</a>"""


# ═══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════

def run_pipeline(vacature_data: dict) -> dict:
    """Volledige pipeline: data → image → HTML → GitHub → Netlify"""

    bedrijf   = vacature_data.get("bedrijfsnaam", "bedrijf").lower().replace(" ", "-")
    functie   = vacature_data.get("functietitel", "vacature").lower().replace(" ", "-")
    sector    = vacature_data.get("sector", "default")
    timestamp = datetime.now().strftime("%Y%m")
    slug      = f"{bedrijf}-{functie}"
    gh_path   = f"pages/{slug}"

    print(f"\n{'='*60}")
    print(f"  VACATUREKANON — Generating: {slug}")
    print(f"  Sector: {sector} | Engine: {IMAGE_ENGINE}")
    print(f"{'='*60}\n")

    # STAP 1: Hero image genereren
    print("📸 STAP 1: Hero image genereren...")
    sector_key = sector if sector in SECTOR_PROMPTS else "default"
    hero_prompt = SECTOR_PROMPTS[sector_key]["hero"]
    hero_bytes = generate_image(hero_prompt)
    print(f"  ✅ Hero image: {len(hero_bytes):,} bytes")

    # STAP 2: Hero image uploaden naar GitHub
    print(f"\n📤 STAP 2: Hero image uploaden naar GitHub...")
    hero_gh_path = f"{gh_path}/hero.jpg"
    hero_url = github_push(
        hero_gh_path,
        hero_bytes,
        f"feat: hero image {slug} [{timestamp}]"
    )
    # Gebruik raw URL voor directe embedding
    hero_raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{hero_gh_path}"
    print(f"  ✅ Hero URL: {hero_raw_url}")

    # STAP 3: HTML genereren
    print(f"\n🔨 STAP 3: HTML genereren...")
    html_content = build_html(vacature_data, hero_raw_url)
    print(f"  ✅ HTML: {len(html_content):,} tekens")

    # STAP 4: HTML uploaden naar GitHub
    print(f"\n📤 STAP 4: HTML uploaden naar GitHub...")
    html_url = github_push(
        f"{gh_path}/index.html",
        html_content.encode("utf-8"),
        f"feat: landing page {slug} v{timestamp} [auto-generated]"
    )
    preview_url = f"https://htmlpreview.github.io/?https://github.com/{GITHUB_REPO}/blob/main/{gh_path}/index.html"
    print(f"  ✅ Preview: {preview_url}")

    # STAP 5: Netlify deploy triggeren (optioneel)
    if NETLIFY_HOOK_URL:
        print(f"\n🚀 STAP 5: Netlify deploy triggeren...")
        req = urllib.request.Request(NETLIFY_HOOK_URL, data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            print(f"  ✅ Netlify deploy gestart: {r.status}")
    else:
        print(f"\n⚠️  STAP 5: Netlify webhook niet ingesteld (sla NETLIFY_HOOK_URL op in .env)")

    result = {
        "slug": slug,
        "gh_path": gh_path,
        "hero_url": hero_raw_url,
        "preview_url": preview_url,
        "generated_at": datetime.now().isoformat()
    }

    print(f"\n{'='*60}")
    print(f"  ✅ KLAAR!")
    print(f"  Preview: {preview_url}")
    print(f"{'='*60}\n")

    return result


# ═══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vacaturekanon Landing Page Generator v2.0")
    parser.add_argument("--input", "-i", help="JSON bestand met vacature data", required=False)
    parser.add_argument("--engine", "-e", choices=["pollinations", "imagen4"], help="Image engine override")
    args = parser.parse_args()

    if args.engine:
        IMAGE_ENGINE = args.engine

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
    else:
        # Demo data (J de Jonge als voorbeeld)
        print("⚠️  Geen --input opgegeven. Demo mode met J de Jonge data.\n")
        data = {
            "bedrijfsnaam": "J de Jonge",
            "bedrijfsnaam_kort": "J",
            "tagline": "Creating The Next-Gen Industry",
            "over_bedrijf": "Sinds 1954 is J de Jonge een vertrouwde leider in EPC-contractering, productie en onderhoud.\nGespecialiseerd in mechanische en piping systemen, laadtechnologie en opslagtank services.\nMet locaties in Nederland, België, Duitsland en Saudi-Arabië zijn we een global enterprise.",
            "website": "https://jdejonge.com",
            "sector": "constructie",
            "opgericht": "1954",
            "medewerkers": "217+",
            "stats": [
                {"waarde": "16.844m²", "label": "Productiecapaciteit"},
                {"waarde": "217+", "label": "Medewerkers"},
                {"waarde": "1954", "label": "Opgericht"},
                {"waarde": "55+", "label": "Culturen"}
            ],
            "functietitel": "Voorman",
            "functietitel_kort": "voorman",
            "locatie": "Nederland",
            "dienstverband": "Fulltime",
            "hero_intro": "Join The Next Gen Connectors. Word onderdeel van een familiebedrijf waar innovatie en samenwerking de toekomst van engineering vormgeven.",
            "taken": [
                "Aansturen en coördineren van montage- en constructieploegen op locatie",
                "Toezicht houden op kwaliteit en voortgang van mechanische en piping projecten",
                "Werkplanningen opstellen en bewaken volgens projecteisen",
                "Communiceren met projectmanagers, opdrachtgevers en onderaannemers",
                "Zorgen voor een veilige werkomgeving (VCA en bedrijfsrichtlijnen)"
            ],
            "eisen": [
                "Minimaal 5 jaar ervaring als voorman in de industriële of EPC-sector",
                "Relevante technische opleiding (MBO/HBO niveau)",
                "VCA-VOL certificaat (of bereid om te behalen)",
                "Ervaring met mechanische installaties, piping en/of storage tanks",
                "Uitstekende communicatieve en leidinggevende vaardigheden",
                "Rijbewijs B, bereid tot reizen binnen Nederland en Europa"
            ],
            "benefits": [
                {"titel": "Competitief Salaris", "tekst": "Marktconform salaris passend bij jouw ervaring", "icon": "💰"},
                {"titel": "Bedrijfsauto", "tekst": "Volledige bedrijfsauto inclusief privégebruik", "icon": "🚗"},
                {"titel": "Flow Academy", "tekst": "Persoonlijke groei via onze eigen Flow Academy", "icon": "📚"},
                {"titel": "Pensioenregeling", "tekst": "Uitstekende pensioenregeling voor een zorgeloze toekomst", "icon": "🛡️"},
                {"titel": "Familie Cultuur", "tekst": "Hechte no-nonsense cultuur met teambuilding events", "icon": "🤝"},
                {"titel": "Internationale Projecten", "tekst": "Werk aan uitdagende projecten in Nederland en Europa", "icon": "🌍"},
                {"titel": "Innovatieve Technologie", "tekst": "Werk met cutting-edge oplossingen", "icon": "⚡"},
                {"titel": "Duurzaamheid", "tekst": "Bijdragen aan duurzame projecten — CO₂ Prestatieladder niveau 3", "icon": "🌱"}
            ],
            "hr_email": "hr@jdejonge.com",
            "hr_telefoon": "+31 (0)10 248 58 00",
            "careers_url": "https://jdejonge.com/careers",
            "jotform_id": ""
        }

    result = run_pipeline(data)
    print(json.dumps(result, indent=2))
