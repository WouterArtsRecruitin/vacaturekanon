#!/usr/bin/env python3
"""
VACATUREKANON — Dynamic Landing Page Generator
Recruitin B.V. | Wouter Arts

Claude Sonnet analyseert elke vacature en genereert een UNIEKE pagina.
Geen templates. Elke pagina heeft eigen kleurpalet, headline, toon, structuur.

Usage:
    python3 generate_dynamic_landing.py \
        --sector "oil-gas" \
        --functie "Senior Procesoperator" \
        --bedrijf "Shell Nederland" \
        --regio "Rotterdam" \
        --niveau "MBO" \
        --urgentie "< 4 weken" \
        --fte "500" \
        --hero-image "https://..." \
        --output "./output/shell-procesoperator.html"
        --deploy  # optioneel: direct naar Netlify
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NETLIFY_TOKEN     = os.getenv("NETLIFY_TOKEN")
NETLIFY_SITE_ID   = os.getenv("NETLIFY_SITE_ID_VACATUREKANON", os.getenv("NETLIFY_SITE_ID"))
MODEL             = "claude-sonnet-4-20250514"

# ── SECTOR INTELLIGENCE ───────────────────────────────────
SECTOR_DNA = {
    "oil-gas": {
        "kleur_primair": "#1A0F00",
        "kleur_accent":  "#F97316",
        "kleur_highlight": "#FBBF24",
        "sfeer": "industrieel, zwaar, technisch, precisie",
        "keywords": ["raffinaderij", "procesinstallaties", "veiligheid", "HSE", "continuproductie"],
        "stats_context": "73% raffinaderijen draait op ondercapaciteit. Gemiddeld 18 maanden om een procesoperator te vinden.",
        "toon": "urgent, direct, vakgericht",
        "hero_stijl": "donker industrieel met oranje accenten",
        "font_karakter": "sterk condensed",
    },
    "constructie": {
        "kleur_primair": "#0F1F2E",
        "kleur_accent":  "#F59E0B",
        "kleur_highlight": "#60A5FA",
        "sfeer": "stoer, resultaatgericht, no-nonsense, teamwerk",
        "keywords": ["bouwproject", "oplevering", "planning", "uitvoering", "veiligheid"],
        "stats_context": "81% bouwbedrijven mist projectdeadlines door personeelstekort. Bouwtechnisch personeel: 6-9 maanden doorlooptijd.",
        "toon": "praktisch, to-the-point, resultaatgericht",
        "hero_stijl": "bouwplaats perspectief met geel/blauw palet",
        "font_karakter": "bold uitgesproken",
    },
    "automation": {
        "kleur_primair": "#0D0D1A",
        "kleur_accent":  "#6366F1",
        "kleur_highlight": "#22D3EE",
        "sfeer": "innovatief, technisch, toekomstgericht, intelligent",
        "keywords": ["PLC", "SCADA", "robotica", "digitalisering", "Industry 4.0"],
        "stats_context": "340 PLC engineers beschikbaar voor 1.200+ openstaande vacatures. Automatiseringsspecialisten: schaars en duur.",
        "toon": "analytisch, toekomstgericht, technisch ambitieus",
        "hero_stijl": "donker tech met paars/cyaan neon accenten",
        "font_karakter": "modern geometrisch",
    },
    "productie": {
        "kleur_primair": "#111A11",
        "kleur_accent":  "#22C55E",
        "kleur_highlight": "#FCD34D",
        "sfeer": "praktisch, teamgericht, efficiëntie, kwaliteit",
        "keywords": ["productielijn", "lean", "kwaliteitscontrole", "teamleiding", "OEE"],
        "stats_context": "68% productiebedrijven draait op minimale bezetting. Teamleiders: gemiddeld 14 maanden vacant.",
        "toon": "direct, menselijk, teamgericht",
        "hero_stijl": "productiehal met groen/geel palet",
        "font_karakter": "sterk leesbaar",
    },
    "renewable-energy": {
        "kleur_primair": "#061A0F",
        "kleur_accent":  "#10B981",
        "kleur_highlight": "#34D399",
        "sfeer": "visionary, impactgericht, duurzaam, toekomst",
        "keywords": ["zonne-energie", "windenergie", "energietransitie", "net-zero", "duurzaamheid"],
        "stats_context": "Nederland heeft 47.000 extra technici nodig voor de energietransitie. Renewable technicians: markt groeit 34% per jaar.",
        "toon": "inspirerend, impactgericht, vooruitstrevend",
        "hero_stijl": "groen/blauw met natuur en technologie",
        "font_karakter": "clean modern",
    },
    "maritime": {
        "kleur_primair": "#030D1A",
        "kleur_accent":  "#00C6FF",
        "kleur_highlight": "#F0A500",
        "sfeer": "internationaal, technisch complex, offshore, wereldwijd",
        "keywords": ["scheepvaart", "offshore", "marine engineering", "aandrijfsystemen", "piping"],
        "stats_context": "Maritime sector groeit 8% per jaar. Gespecialiseerde marine engineers: wereldwijd schaarste.",
        "toon": "technisch premium, internationaal, ambitieus",
        "hero_stijl": "donkerblauw industrieel maritiem met cyaan accenten",
        "font_karakter": "strak technisch",
    },
    "default": {
        "kleur_primair": "#111827",
        "kleur_accent":  "#F97316",
        "kleur_highlight": "#FCD34D",
        "sfeer": "professioneel, betrouwbaar, resultaatgericht",
        "keywords": ["expertise", "groei", "team", "uitdaging"],
        "stats_context": "Nederlandse arbeidsmarkt onder druk. Technisch personeel gemiddeld 6-12 maanden om te vinden.",
        "toon": "professioneel, direct",
        "hero_stijl": "donker professioneel",
        "font_karakter": "clean modern",
    }
}

NIVEAU_PROFIEL = {
    "MBO":      {"toon_extra": "direct, praktisch, no-nonsense. Vermijd jargon.", "cta": "Reageer direct", "badge": "Vakman gezocht"},
    "HBO":      {"toon_extra": "analytisch maar toegankelijk. Mix van praktijk en theorie.", "cta": "Solliciteer nu", "badge": "Specialist gezocht"},
    "WO":       {"toon_extra": "analytisch, strategisch, academisch onderbouwd.", "cta": "Bekijk de functie", "badge": "Senior functie"},
    "Directie": {"toon_extra": "strategisch, visionary, high-level. C-suite taal.", "cta": "Neem contact op", "badge": "Management rol"},
    "default":  {"toon_extra": "helder en toegankelijk.", "cta": "Solliciteer nu", "badge": "Vacature"},
}

URGENTIE_COPY = {
    "< 4 weken":    {"urgentie_badge": "🔴 Urgente vacature", "urgentie_tekst": "Kandidaat gezocht binnen 4 weken"},
    "1-2 maanden":  {"urgentie_badge": "🟠 Actief wervend",   "urgentie_tekst": "Selectieproces loopt nu"},
    "2-3 maanden":  {"urgentie_badge": "🟡 Werving gestart",  "urgentie_tekst": "Vroegtijdig solliciteren loont"},
    "Geen haast":   {"urgentie_badge": "🟢 Open sollicitatie","urgentie_tekst": "Altijd interesse in talent"},
    "default":      {"urgentie_badge": "📋 Vacature open",    "urgentie_tekst": "Reageer op deze vacature"},
}


def get_sector_dna(sector: str) -> dict:
    sector_key = sector.lower().replace(" ", "-").replace("_", "-")
    for key in SECTOR_DNA:
        if key in sector_key:
            return SECTOR_DNA[key]
    return SECTOR_DNA["default"]


def build_design_prompt(data: dict, sector_dna: dict, niveau_profiel: dict, urgentie_info: dict) -> str:
    return f"""Je bent een expert recruitment UX designer en copywriter voor de Nederlandse B2B markt.

Genereer een COMPLETE, UNIEKE vacature landing page in HTML/CSS/JS voor:

## VACATURE INPUT
- Functie: {data['functie']}
- Sector: {data['sector']}
- Bedrijf: {data['bedrijf']}
- Regio: {data['regio']}
- Niveau: {data.get('niveau', 'HBO')}
- Urgentie: {data.get('urgentie', '1-2 maanden')}
- Medewerkers (FTE): {data.get('fte', 'onbekend')}
- Hero image URL: {data.get('hero_image', '')}
- Salaris range: {data.get('salaris', 'marktconform')}
- Extra info: {data.get('extra', '')}

## DESIGN DNA — SECTOR: {data['sector'].upper()}
- Kleur primair (achtergrond): {sector_dna['kleur_primair']}
- Kleur accent (buttons/highlights): {sector_dna['kleur_accent']}
- Kleur highlight (keywords in tekst): {sector_dna['kleur_highlight']}
- Sfeer: {sector_dna['sfeer']}
- Toon van schrijven: {sector_dna['toon']}
- Toon aanpassing voor niveau {data.get('niveau','HBO')}: {niveau_profiel['toon_extra']}
- Hero visuele stijl: {sector_dna['hero_stijl']}
- Font karakter: {sector_dna['font_karakter']}
- Sector statistiek context: {sector_dna['stats_context']}

## URGENTIE
- Badge: {urgentie_info['urgentie_badge']}
- Subtekst: {urgentie_info['urgentie_tekst']}

## VERPLICHTE SECTIES (in deze volgorde)
1. NAVBAR — Logo ({data['bedrijf'][:2].upper()}), hamburger menu, urgentie pill
2. HERO — Fullscreen met hero image of sector gradient, grote headline met 2 gekleurde keywords, subtitel, locatie/type meta, 2 CTAs
3. STATS STRIP — 4 bedrijfsstatistieken (gebruik sector context + bedrijfsgrootte {data.get('fte','?')} FTE)
4. OVER SECTIE — Bedrijfsintro met accent op keyword, 2 alinea's
5. QUOTE SECTIE — Fictieve medewerker quote passend bij de sector + naam/functie
6. FUNCTIE KENMERKEN GRID — 4 cards: Locatie, Contract, Salaris ({data.get('salaris','marktconform')}), Niveau
7. PROFIEL CHECKLIST — 5-7 vereisten passend bij {data['functie']} op {data.get('niveau','HBO')} niveau
8. CTA SECTIE — Solliciteer card + WhatsApp button
9. FOOTER — Bedrijfslogo + "Geplaatst door Recruitin B.V."

## TECHNISCHE EISEN
- Volledig responsief mobile-first (primair smartphone)
- Google Font via CDN: kies EEN font dat past bij "{sector_dna['font_karakter']}" — NIET Inter of Roboto
- CSS custom properties (--var) voor kleuren
- Smooth scroll + navbar scrolled state
- IntersectionObserver voor fade-in animaties
- Hero: als hero_image URL aanwezig → gebruik die als background-image. Anders → CSS gradient passend bij sector
- Alle placeholders voor automation: {{SOLLICITEER_URL}}, {{WHATSAPP_URL}}, {{META_PIXEL_ID}}
- Open Graph meta tags bovenaan

## COPY REGELS
- Schrijf in het NEDERLANDS
- Headline: max 8 woorden, 2 keywords in accentkleur
- Gebruik sector-specifieke taal ({', '.join(sector_dna['keywords'][:3])})
- CTA tekst: "{niveau_profiel['cta']}" — urgent maar niet opdringerig
- Geen generieke bullshit als "uitdagende functie" of "marktconform salaris" tenzij dat het enige is

## OUTPUT
Geef ALLEEN de volledige HTML terug. Geen uitleg. Geen markdown. Geen code blocks.
Begin direct met <!DOCTYPE html> en eindig met </html>.
De pagina moet 100% standalone werken zonder externe dependencies behalve Google Fonts.
"""


def generate_html_with_claude(prompt: str) -> str:
    """Roep Claude Sonnet API aan voor HTML generatie."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY niet ingesteld")

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 8000,
            "messages": [{"role": "user", "content": prompt}],
            "system": "Je bent een expert frontend developer en recruitment copywriter. Je genereert altijd volledige, werkende HTML zonder markdown of uitleg. Alleen pure HTML van <!DOCTYPE html> tot </html>."
        },
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError(f"Claude API error {response.status_code}: {response.text}")

    data = response.json()
    html = data["content"][0]["text"].strip()

    # Strip eventuele markdown code blocks
    if html.startswith("```"):
        lines = html.split("\n")
        html = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    return html


def deploy_to_netlify(html_content: str, site_name: str) -> str:
    """Deploy HTML als nieuwe Netlify site of update bestaande."""
    if not NETLIFY_TOKEN:
        raise ValueError("NETLIFY_TOKEN niet ingesteld")

    # Maak zip van HTML als index.html
    import zipfile
    import io

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", html_content)
    zip_buffer.seek(0)

    # Check of site al bestaat
    sites_resp = requests.get(
        "https://api.netlify.com/api/v1/sites",
        headers={"Authorization": f"Bearer {NETLIFY_TOKEN}"},
        params={"filter": "all"}
    )

    site_id = None
    if sites_resp.status_code == 200:
        for site in sites_resp.json():
            if site.get("name") == site_name:
                site_id = site["id"]
                break

    # Deploy
    if site_id:
        # Update bestaande site
        deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
    else:
        # Nieuwe site aanmaken
        create_resp = requests.post(
            "https://api.netlify.com/api/v1/sites",
            headers={"Authorization": f"Bearer {NETLIFY_TOKEN}", "Content-Type": "application/json"},
            json={"name": site_name}
        )
        if create_resp.status_code not in (200, 201):
            raise RuntimeError(f"Netlify site aanmaken mislukt: {create_resp.text}")
        site_id = create_resp.json()["id"]
        deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"

    deploy_resp = requests.post(
        deploy_url,
        headers={
            "Authorization": f"Bearer {NETLIFY_TOKEN}",
            "Content-Type": "application/zip",
        },
        data=zip_buffer.getvalue()
    )

    if deploy_resp.status_code not in (200, 201):
        raise RuntimeError(f"Netlify deploy mislukt: {deploy_resp.text}")

    deploy_data = deploy_resp.json()
    live_url = deploy_data.get("deploy_ssl_url") or deploy_data.get("ssl_url") or f"https://{site_name}.netlify.app"
    return live_url


def generate_site_name(bedrijf: str, functie: str) -> str:
    """Genereer een Netlify-vriendelijke sitenaam."""
    import re
    name = f"{bedrijf}-{functie}".lower()
    name = re.sub(r"[^a-z0-9-]", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    timestamp = datetime.now().strftime("%m%d")
    return f"vk-{name[:40]}-{timestamp}"


def main():
    parser = argparse.ArgumentParser(description="Vacaturekanon Dynamic Landing Page Generator")
    parser.add_argument("--sector",     required=True,  help="Sector (oil-gas, constructie, automation, productie, renewable-energy, maritime)")
    parser.add_argument("--functie",    required=True,  help="Functietitel")
    parser.add_argument("--bedrijf",    required=True,  help="Bedrijfsnaam")
    parser.add_argument("--regio",      default="Nederland", help="Regio/locatie")
    parser.add_argument("--niveau",     default="HBO",   help="Functieniveau (MBO/HBO/WO/Directie)")
    parser.add_argument("--urgentie",   default="1-2 maanden", help="Urgentie")
    parser.add_argument("--fte",        default="",     help="Aantal medewerkers FTE")
    parser.add_argument("--salaris",    default="marktconform", help="Salaris range")
    parser.add_argument("--hero-image", default="",     help="URL van hero image (Kling output)")
    parser.add_argument("--extra",      default="",     help="Extra context over de vacature")
    parser.add_argument("--output",     default="./output.html", help="Output HTML bestandspad")
    parser.add_argument("--deploy",     action="store_true", help="Direct deployen naar Netlify")
    parser.add_argument("--json",       default="",     help="JSON string met alle data (alternatief voor losse args)")
    args = parser.parse_args()

    # Data samenstellen
    if args.json:
        data = json.loads(args.json)
    else:
        data = {
            "sector":      args.sector,
            "functie":     args.functie,
            "bedrijf":     args.bedrijf,
            "regio":       args.regio,
            "niveau":      args.niveau,
            "urgentie":    args.urgentie,
            "fte":         args.fte,
            "salaris":     args.salaris,
            "hero_image":  getattr(args, "hero_image", ""),
            "extra":       args.extra,
        }

    print(f"\n🎯 Vacaturekanon Generator")
    print(f"   Functie:  {data['functie']}")
    print(f"   Bedrijf:  {data['bedrijf']}")
    print(f"   Sector:   {data['sector']}")
    print(f"   Niveau:   {data['niveau']}")

    # Design DNA ophalen
    sector_dna    = get_sector_dna(data["sector"])
    niveau_profiel = NIVEAU_PROFIEL.get(data.get("niveau", "default"), NIVEAU_PROFIEL["default"])
    urgentie_info  = URGENTIE_COPY.get(data.get("urgentie", "default"), URGENTIE_COPY["default"])

    print(f"\n🎨 Design: {sector_dna['hero_stijl']}")
    print(f"   Kleur:   {sector_dna['kleur_accent']}")
    print(f"   Toon:    {sector_dna['toon']}")
    print(f"\n⚡ Claude Sonnet genereert unieke pagina...")

    # Prompt bouwen
    prompt = build_design_prompt(data, sector_dna, niveau_profiel, urgentie_info)

    # HTML genereren
    try:
        html = generate_html_with_claude(prompt)
        print(f"   ✅ HTML gegenereerd ({len(html):,} tekens)")
    except Exception as e:
        print(f"   ❌ Claude API fout: {e}")
        sys.exit(1)

    # Opslaan
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"   💾 Opgeslagen: {output_path}")

    # Optioneel deployen
    if args.deploy:
        site_name = generate_site_name(data["bedrijf"], data["functie"])
        print(f"\n🚀 Deployen naar Netlify als '{site_name}'...")
        try:
            live_url = deploy_to_netlify(html, site_name)
            print(f"   ✅ Live: {live_url}")

            # Resultaat als JSON teruggeven voor de webhook handler
            result = {
                "ok": True,
                "live_url": live_url,
                "site_name": site_name,
                "functie": data["functie"],
                "bedrijf": data["bedrijf"],
                "sector": data["sector"],
                "generated_at": datetime.now().isoformat(),
            }
            print(f"\n📋 JSON output:")
            print(json.dumps(result, indent=2))

        except Exception as e:
            print(f"   ❌ Netlify deploy fout: {e}")
            sys.exit(1)
    else:
        print(f"\n💡 Tip: voeg --deploy toe voor directe Netlify publicatie")

    print(f"\n✅ Klaar!")


if __name__ == "__main__":
    main()
