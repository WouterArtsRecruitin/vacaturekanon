#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
📊 KANDIDATENTEKORT.NL — UNIFIED V8 ENGINE
═══════════════════════════════════════════════════════════════

UNIFIED FLOW:
Jotform → Supabase → Claude Sonnet V3.1 → ICP Scoring →
HTML Rapport (V1 Executive + V2 Storytelling) → Resend Email →
Pipedrive (qualified only) → Lemlist Nurture (split)

Author: Wouter Arts / Claude
Version: 8.0 (Template-Based)
═══════════════════════════════════════════════════════════════
"""

import os, io, re, json, datetime, subprocess, tempfile, requests
from dotenv import load_dotenv
import anthropic

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kt_env")
load_dotenv(env_path, override=True)

SUPABASE_URL    = os.environ.get("SUPABASE_URL")
SUPABASE_KEY    = os.environ.get("SUPABASE_KEY")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY")
RESEND_KEY      = os.environ.get("RESEND_API_KEY")
JOTFORM_KEY     = os.environ.get("JOTFORM_API_KEY")
PIPEDRIVE_TOKEN = os.environ.get("PIPEDRIVE_API_TOKEN")
PIPEDRIVE_DOMAIN= os.environ.get("PIPEDRIVE_DOMAIN", "recruitinbv")
LEMLIST_KEY     = os.environ.get("LEMLIST_API_KEY")
LEMLIST_CAMPAIGN_QUALIFIED = os.environ.get("KT_LEMLIST_CAMPAIGN_QUALIFIED", os.environ.get("LEMLIST_CAMPAIGN_ID"))
LEMLIST_CAMPAIGN_NURTURE   = os.environ.get("KT_LEMLIST_CAMPAIGN_NURTURE", os.environ.get("LEMLIST_CAMPAIGN_ID"))
CALENDLY        = "https://calendly.com/wouter-arts-/vacature-analyse-advies"
PIPEDRIVE_BASE  = f"https://{PIPEDRIVE_DOMAIN}.pipedrive.com/v1"
ICP_THRESHOLD   = 65

TEMPLATE_DIR = "/Users/wouterarts/recruitin/templates"

# ═══════════════════════════════════════════════════════════════
# 🎯 MASTER PROMPT V3.1 (STORYTELLING + TEMPLATE VARIABLE OUTPUT)
# ═══════════════════════════════════════════════════════════════

PROMPT_V31 = """Je bent een senior vacaturetekst specialist gespecialiseerd in TECHNISCHE EN INDUSTRIËLE SECTOREN.

Gecertificeerd: Intelligence Group VacatureVerbeteraar (niveau 4)
Ervaring: 12+ jaar Nederlandse arbeidsmarkt | Data: 2500+ vacatures (2024-2025)

SECTOR FOCUS: Oil & Gas, Manufacturing, Automation, Renewable Energy, Construction
BEDRIJFSMAAT: 50-800 medewerkers | REGIO'S: Gelderland, Overijssel, Noord-Brabant

2025 ARBEIDSMARKT:
- 68% tekorten | TTF: 52 dagen | 70% mobile | 89% verwacht <24u reactie
- Vacatures MET salaris: +64% meer sollicitaties

8-DIMENSIONALE SCORECARD (weging):
1. Aantrekkelijkheid 15% (bench 4.5) | 2. Duidelijkheid 15% (5.2) | 3. Volledigheid 12% (4.8)
4. Salaris Transparantie 18% (3.1) | 5. Sollicitatie UX 12% (5.5) | 6. SEO 10% (4.2)
7. Employer Branding 8% (4.0) | 8. Kandidaat Ervaring 10% (4.3)

═══════════════════════════════════════════════════════════════
ANALYSEER DEZE VACATURETEKST:
Bedrijf: {bedrijf}
Vacaturetekst:
{vacature_text}
═══════════════════════════════════════════════════════════════

LEVER DE OUTPUT ALS PURE JSON — GEEN MARKDOWN, GEEN UITLEG, ALLEEN EEN VALIDE JSON OBJECT.
De JSON moet EXACT deze structuur hebben. Alle waarden zijn strings tenzij anders aangegeven.

```json
{{
  "header": {{
    "score": "6.8",
    "score_percentage": "68%",
    "trend": "↑ Stijgend",
    "expected_conversion_min": "3",
    "expected_conversion_max": "5",
    "ttf_min": "40",
    "ttf_max": "55"
  }},
  "vacancy": {{
    "functie_titel": "Allround Technicus Procesindustrie",
    "bedrijf_naam": "Veco B.V.",
    "sector": "Manufacturing",
    "functie_niveau": "Medior",
    "locatie": "Eerbeek",
    "regio": "Gelderland",
    "salaris_min": "42000",
    "salaris_max": "54600",
    "sector_premium": "0"
  }},
  "scorecard": {{
    "score_1": "4.5", "gap_1": "+0.0", "status_1": "⚠️ MEDIUM",
    "score_2": "6.0", "gap_2": "+0.8", "status_2": "✅ GOED",
    "score_3": "5.5", "gap_3": "+0.7", "status_3": "✅ GOED",
    "score_4": "1.0", "gap_4": "-2.1", "status_4": "❌ KRITIEK",
    "score_5": "3.0", "gap_5": "-2.5", "status_5": "❌ KRITIEK",
    "score_6": "4.5", "gap_6": "+0.3", "status_6": "⚠️ MEDIUM",
    "score_7": "4.0", "gap_7": "+0.0", "status_7": "⚠️ MEDIUM",
    "score_8": "3.5", "gap_8": "-0.8", "status_8": "❌ KRITIEK"
  }},
  "conclusie": {{
    "samenvatting_probleem": "De data liegt niet: de huidige vacaturetekst verliest je kandidaten hoofdzakelijk af op <strong>Salaristransparantie (2.0)</strong> en <strong>Employer Branding (3.2)</strong>. Kortom:...",
    "samenvatting_oplossing": "duidelijke financiële verwachtingen te creëren en de werkplaats-identiteit agressiever in de markt te zetten."
  }},
  "blockers": {{
    "blocker_1_titel": "Salaris ontbreekt",
    "blocker_1_oorzaak": "Kandidaten haken direct af als de salarisbandbreedte een mysterie is.",
    "blocker_2_titel": "...",
    "blocker_2_oorzaak": "...",
    "blocker_3_titel": "...",
    "blocker_3_oorzaak": "..."
  }},
  "quick_wins": {{
    "quick_win_1_titel": "Salaris bereik toevoegen",
    "quick_win_1_uitleg": "De concurrent toont direct cijfers, waardoor een technicus niet hoeft te gissen. Vage termen als 'marktconform' creëren wantrouwen.",
    "quick_win_1_voor": "Exacte foute zin uit origineel (bijv. 'Marktconform salaris')",
    "quick_win_1_na": "Directe verbetering (bijv. '€3.500 - €4.550 bruto per maand')",
    "quick_win_2_titel": "...",
    "quick_win_2_uitleg": "...",
    "quick_win_2_voor": "...",
    "quick_win_2_na": "...",
    "quick_win_3_titel": "...",
    "quick_win_3_uitleg": "...",
    "quick_win_3_voor": "...",
    "quick_win_3_na": "..."
  }},
  "roadmap": {{
    "roadmap_week1_titel": "Vacature Online Zetten",
    "roadmap_week1_content": "Plaats de vernieuwde vacaturetekst stipt woord-voor-woord over op je eigen site.",
    "roadmap_week2_titel": "...",
    "roadmap_week2_content": "...",
    "roadmap_week3_titel": "...",
    "roadmap_week3_content": "...",
    "roadmap_week4_titel": "...",
    "roadmap_week4_content": "..."
  }},
  "storytelling": {{
    "opening_hook_line_1": "Maandagochtend 06:30. Lange lopende hook zin die de lezer direct meeneemt in een werkdag-scenario...",
    "opening_hook_line_2": "Tweede alinea die het verhaal verder uitwerkt en de context schetst...",
    "challenge_intro_paragraph": "Storytelling paragraaf over de uitdaging — wat ga je doen en waarom is het belangrijk...",
    "job_responsibilities_paragraph": "Verhalende beschrijving van dagelijkse taken, GEEN bullets...",
    "team_collaboration_highlight": "Quote of highlight over team samenwerking — concreet en menselijk...",
    "job_uniqueness_paragraph": "Wat maakt deze rol uniek — show don't tell...",
    "experience_intro_paragraph": "Verhalende beschrijving van wie de ideale kandidaat is...",
    "technical_requirements_title": "Technische Basis",
    "technical_requirements_list": "<li>MBO niveau 3+ Elektrotechniek/Mechatronica</li><li>3-5 jaar procesindustrie ervaring</li><li>PLC programmeerervaring</li>",
    "mindset_requirements_title": "Mindset & Attitude",
    "mindset_requirements_list": "<li>Oplossingsgericht denken</li><li>Nieuwsgierig en leergierig</li><li>Hoog veiligheidsbewustzijn</li>",
    "character_description_paragraph": "Beschrijving van het karakter en de persoonlijkheid die past...",
    "nice_to_have_paragraph": "Nice-to-have kwalificaties in verhalende vorm...",
    "salary_range_text": "€3.500 - €4.550 bruto per maand",
    "salary_transparency_message": "Op basis van jouw ervaring en certificeringen. We zijn transparant over wat je verdient.",
    "benefits_intro_text": "Naast je salaris krijg je:",
    "benefits_list_items": "<li><strong>8% vakantiegeld</strong> — bovengemiddeld</li><li><strong>27 vakantiedagen + 13 ADV</strong></li><li><strong>Winstdeling</strong> — als het bedrijf presteert, profiteer jij mee</li>",
    "total_package_intro_text": "Maar geld is niet alles. Wat we echt bieden is...",
    "company_culture_paragraph": "Beschrijving van de bedrijfscultuur in storytelling stijl...",
    "growth_path_intro_text": "Veel vacatures beloven doorgroeimogelijkheden. Hier is concreet wat we bedoelen:",
    "pathway_year_1_title": "Jaar 1-2: Specialisatie",
    "pathway_year_1_description": "Beschrijving van wat je leert in de eerste twee jaar...",
    "pathway_year_1_outcome": "→ Specialist niveau bereikt",
    "pathway_year_2_title": "Jaar 3-4: Verdieping",
    "pathway_year_2_description": "Beschrijving van verdieping en extra verantwoordelijkheden...",
    "pathway_year_2_outcome": "→ Senior of Lead positie",
    "pathway_year_3_title": "Jaar 5+: Leiderschap",
    "pathway_year_3_description": "Beschrijving van leadership trajectory...",
    "pathway_year_3_outcome": "→ Team Lead / Engineering rol",
    "training_budget_paragraph": "We investeren €X per jaar per technicus in opleiding en certificeringen...",
    "company_why_intro_text": "Waarom zou je juist hier willen werken? Eerlijk antwoord...",
    "company_unique_value_proposition": "De unieke waardepropositie van dit bedrijf in concrete termen...",
    "company_impact_intro_text": "Wat betekent jouw werk concreet? Hier zijn voorbeelden...",
    "company_impact_examples": "<div class='comparison-row'><div class='comparison-icon'>🔧</div><div class='comparison-text-item'><strong>Impact 1:</strong> Concrete beschrijving</div></div>",
    "company_impact_closing_paragraph": "Afsluitende paragraaf over de bredere impact van het werk...",
    "apply_interest_text": "Geïnteresseerd? Dit is hoe het werkt...",
    "contact_info_paragraph": "Bel direct met [naam] op [nummer] of stuur een WhatsApp.",
    "application_process_text": "Stap 1: Solliciteer (2 min) → Stap 2: Belafspraak binnen 24u → Stap 3: Rondleiding + gesprek → Stap 4: Start",
    "background_check_text": ""
  }},
  "icp": {{
    "sector_match": true,
    "regio_match": true,
    "grootte_indicator": "medium",
    "technisch_niveau": "hoog",
    "budget_indicator": "gemiddeld",
    "icp_score": 72,
    "verdict": "QUALIFIED"
  }}
}}
```

BELANGRIJK:
- Vul ALLE velden in met ECHTE, relevante data gebaseerd op de vacature
- Storytelling secties MOETEN in vloeiende, narratieve tekst zijn (GEEN bullets behalve requirements/benefits)
- Open de storytelling met een CONCREET WERKDAG-SCENARIO (show, don't tell)
- Schrijf alsof een collega-monteur het vertelt — nuchter, direct, vakmanschap
- ICP score: 0-100 gebaseerd op sector fit, regio, grootte en technisch niveau
- De blockers en quick_wins output wordt DIRECT in koude e-mails (Lemlist) gebruikt. Zorg dat de oorzaken 100% e-mailklaar, direct, en kort & punchy zijn.
- Geef ALLEEN valid JSON terug, geen markdown codeblocks, geen uitleg
"""

# ═══════════════════════════════════════════════════════════════
# 🔧 HELPERS
# ═══════════════════════════════════════════════════════════════

def sb_headers():
    return {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/json"}

def sb_get(path):
    return requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers())

def sb_patch(table, id, data):
    return requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{id}", headers=sb_headers(), json=data)

def load_template(filename):
    path = os.path.join(TEMPLATE_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def fill_template(template_html, variables):
    """Vervang alle {{variable}} placeholders met echte waarden."""
    result = template_html
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result

# ═══════════════════════════════════════════════════════════════
# 📄 TEMPLATE-BASED RAPPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

def build_v1_executive(voornaam, bedrijf, ai_data, lid):
    """Bouw het V1 Executive Summary rapport met de echte HTML template."""
    template = load_template("generieke_rapport_template_v1_executive.html")
    
    h = ai_data.get("header", {})
    v = ai_data.get("vacancy", {})
    sc = ai_data.get("scorecard", {})
    co = ai_data.get("conclusie", {})
    qw = ai_data.get("quick_wins", {})
    rm = ai_data.get("roadmap", {})
    
    variables = {
        "analyse_datum": datetime.datetime.now().strftime("%d %B %Y"),
        "analyse_id": f"KT-{datetime.datetime.now().strftime('%Y%m%d')}-{bedrijf[:3].upper()}",
        "score": h.get("score", "??"),
        "score_percentage": h.get("score_percentage", ""),
        "trend": h.get("trend", "→"),
        "expected_conversion_min": h.get("expected_conversion_min", ""),
        "expected_conversion_max": h.get("expected_conversion_max", ""),
        "ttf_min": h.get("ttf_min", ""),
        "ttf_max": h.get("ttf_max", ""),
        "functie_titel": v.get("functie_titel", ""),
        "bedrijf_naam": bedrijf,
        "sector": v.get("sector", ""),
        "functie_niveau": v.get("functie_niveau", ""),
        "locatie": v.get("locatie", ""),
        "regio": v.get("regio", ""),
        "salaris_min": v.get("salaris_min", ""),
        "salaris_max": v.get("salaris_max", ""),
        "sector_premium": v.get("sector_premium", "0"),
        # Scorecard
        **{k: sc.get(k, "") for k in [f"score_{i}" for i in range(1,9)] + [f"gap_{i}" for i in range(1,9)] + [f"status_{i}" for i in range(1,9)]},
        # Conclusie
        "samenvatting_probleem": co.get("samenvatting_probleem", ""),
        "samenvatting_oplossing": co.get("samenvatting_oplossing", ""),
        # Quick wins
        **{k: qw.get(k, "") for k in [f"quick_win_{i}_{f}" for i in range(1,4) for f in ["titel","uitleg","voor","na"]]},
        # Roadmap
        **{k: rm.get(k, "") for k in [f"roadmap_week{i}_{f}" for i in range(1,5) for f in ["titel","content"]]},
        # CTA
        "cta_heading": "Klaar om jouw vacature te laten converteren?",
        "calendly_link": f"https://kandidatentekort.nl/intake.html?id={lid}",
        "cta_button_text": "📞 Plan Adviesgesprek",
        "link_rapport": f"https://kandidatentekort.nl/rapport.html?id={lid}&type=storytelling",
        # Footer
        "contact_naam": "Wouter Arts",
        "contact_phone": "06-12345678",
    }
    
    return fill_template(template, variables)


def build_v2_storytelling(ai_data, bedrijf):
    """Bouw het V2 Storytelling Vacaturetekst rapport met de echte HTML template."""
    template = load_template("generieke_rapport_template_v2_vacaturetekst.html")
    
    v = ai_data.get("vacancy", {})
    st = ai_data.get("storytelling", {})
    
    variables = {
        "functie_titel": v.get("functie_titel", ""),
        "bedrijf_naam": bedrijf,
        "locatie": v.get("locatie", ""),
        "regio": v.get("regio", ""),
        "functie_niveau": v.get("functie_niveau", ""),
        "salaris_min": v.get("salaris_min", ""),
        "salaris_max": v.get("salaris_max", ""),
        "sector": v.get("sector", ""),
        # Storytelling — alle velden
        **{k: st.get(k, "") for k in st.keys()},
        # CTA
        "cta_banner_heading": "Klaar om te solliciteren?",
        "cta_banner_subheading": "Neem vandaag nog contact op — we reageren binnen 24 uur.",
        "sollicitatie_link": CALENDLY,
        "contact_link": CALENDLY,
        "cta_button_apply_text": "Solliciteer Direct",
        "cta_button_info_text": "Stel een Vraag",
        # Footer
        "analyse_datum": datetime.datetime.now().strftime("%d %B %Y"),
        "contact_naam": "Wouter Arts",
        "contact_phone": "06-12345678",
    }
    
    return fill_template(template, variables)

# ═══════════════════════════════════════════════════════════════
# 📧 TEASER EMAIL (Resend)
# ═══════════════════════════════════════════════════════════════

def build_teaser_email(voornaam, bedrijf, ai_data, report_url):
    h = ai_data.get("header", {})
    bl = ai_data.get("blockers", {})
    qw = ai_data.get("quick_wins", {})
    score = h.get("score", "??")
    
    try:
        s = float(score)
        score_color = "#10B981" if s >= 7 else "#3B82F6" if s >= 5.5 else "#F59E0B" if s >= 4 else "#EF4444"
        label = "Uitstekend" if s >= 8 else "Goed" if s >= 6.5 else "Kan flink beter" if s >= 5 else "Conversie Killer"
    except:
        score_color, label = "#6B7280", "Geanalyseerd"

    blockers_html = ""
    for i in range(1, 4):
        titel = bl.get(f"blocker_{i}_titel", "")
        if titel:
            blockers_html += f'<tr><td style="padding:10px 0;border-bottom:1px solid #FDE68A;"><span style="display:inline-block;width:28px;height:28px;background:#EF4444;border-radius:14px;text-align:center;color:white;font-weight:bold;line-height:28px;margin-right:10px;">{i}</span><strong>{titel}</strong> — {bl.get(f"blocker_{i}_oorzaak", "")[:120]}</td></tr>'

    voor = qw.get("quick_win_1_voor", "")
    na = qw.get("quick_win_1_na", "")

    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;">
<tr><td align="center" style="padding:30px 15px;">
<table width="650" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 10px rgba(0,0,0,0.05);">

<tr><td style="background:#0F172A;padding:35px 40px;">
<table width="100%"><tr>
<td width="50"><div style="width:48px;height:48px;background:#FF6B35;border-radius:24px;text-align:center;font-size:22px;font-weight:bold;color:#fff;line-height:48px;">R</div></td>
<td style="padding-left:14px;"><p style="margin:0;color:#fff;font-size:20px;font-weight:bold;">RECRUITIN</p><p style="margin:2px 0 0;color:#94A3B8;font-size:12px;text-transform:uppercase;">Vacature Intelligence Platform</p></td>
</tr></table>
</td></tr>

<tr><td style="padding:35px 40px 25px;">
<p style="font-size:20px;font-weight:bold;color:#1F2937;margin:0 0 12px;">Hoi {voornaam},</p>
<p style="font-size:15px;color:#4B5563;line-height:1.6;margin:0 0 12px;">We hebben jouw vacature voor <strong>{bedrijf}</strong> door onze Recruitment Intelligence Engine gehaald.</p>
</td></tr>

<tr><td style="padding:0 40px 30px;" align="center">
<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:30px;">
<p style="margin:0 0 5px;font-size:52px;font-weight:900;color:{score_color};">{score}<span style="font-size:18px;color:#9CA3AF;">/10</span></p>
<span style="display:inline-block;background:{score_color}20;border:2px solid {score_color};border-radius:20px;padding:6px 20px;font-size:14px;font-weight:bold;color:{score_color};">{label}</span>
</div>
</td></tr>

<tr><td style="padding:0 40px 30px;">
<div style="background:#FFFBEB;border-left:4px solid #F59E0B;border-radius:0 8px 8px 0;padding:20px 25px;">
<p style="margin:0 0 12px;font-size:16px;font-weight:bold;color:#92400E;">🎯 De Grootste Conversie-Killers</p>
<table width="100%">{blockers_html}</table>
</div>
</td></tr>

<tr><td style="padding:0 40px 30px;">
<p style="font-size:12px;color:#6366F1;font-weight:bold;text-transform:uppercase;margin:0 0 6px;">Quick Win #1</p>
<table width="100%"><tr>
<td width="48%" valign="top" style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:20px;">
<p style="margin:0 0 8px;font-size:12px;font-weight:bold;color:#DC2626;text-transform:uppercase;">❌ Nu</p>
<p style="margin:0;font-size:13px;color:#7F1D1D;line-height:1.5;font-family:Monaco,monospace;">{voor}</p>
</td>
<td width="4%"></td>
<td width="48%" valign="top" style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:8px;padding:20px;">
<p style="margin:0 0 8px;font-size:12px;font-weight:bold;color:#059669;text-transform:uppercase;">✅ Na optimalisatie</p>
<p style="margin:0;font-size:13px;color:#064E3B;line-height:1.5;font-family:Monaco,monospace;">{na}</p>
</td>
</tr></table>
</td></tr>

<tr><td style="padding:0 40px 40px;">
<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:30px;text-align:center;">
<p style="font-size:18px;font-weight:bold;color:#0F172A;margin:0 0 10px;">Jouw Volledige Rapport is Klaar</p>
<p style="font-size:14px;color:#4B5563;margin:0 0 20px;">Scorecard, verbeterde storytelling vacaturetekst, 30-dagen roadmap.</p>
<a href="{report_url}" style="display:inline-block;padding:14px 28px;background:#1E3A8A;color:#fff;text-decoration:none;border-radius:6px;font-weight:bold;font-size:15px;">📄 Bekijk Volledig Rapport</a>
<p style="margin:15px 0 0;font-size:13px;color:#52525B;">Of <a href="{CALENDLY}" style="color:#FF6B35;font-weight:bold;text-decoration:none;">plan een korte intake 📞</a></p>
</div>
</td></tr>

<tr><td style="background:#0F172A;padding:25px 40px;text-align:center;">
<p style="margin:0;color:#64748B;font-size:11px;">© 2026 Kandidatentekort.nl | B2B Recruitment Automation | Recruitin B.V.</p>
</td></tr>

</table></td></tr></table></body></html>'''

# ═══════════════════════════════════════════════════════════════
# 📥 FILE HANDLING
# ═══════════════════════════════════════════════════════════════

def download_jotform_file(file_url, lead_id):
    if not file_url or not file_url.startswith("http"):
        return None, file_url or ""
    try:
        resp = requests.get(file_url, params={"apiKey": JOTFORM_KEY}, timeout=30)
        if resp.ok:
            content = resp.content
            ext = ".pdf" if file_url.lower().endswith(".pdf") else ".docx"
            storage_path = f"{lead_id}/vacature{ext}"
            requests.post(f"{SUPABASE_URL}/storage/v1/object/kt_vacatures/{storage_path}",
                headers={"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY, "Content-Type": "application/octet-stream"},
                data=content)
            return content, f"{SUPABASE_URL}/storage/v1/object/public/kt_vacatures/{storage_path}"
    except Exception as e:
        print(f"  Download error: {e}")
    return None, file_url

def extract_text(content, file_url):
    if not content: return ""
    if file_url.lower().endswith('.pdf'):
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                tf.write(content); tf_path = tf.name
            result = subprocess.run(["/opt/homebrew/bin/pdftotext", "-layout", tf_path, "-"], capture_output=True, text=True)
            try: os.remove(tf_path)
            except: pass
            return result.stdout.strip() or "PDF bevatte geen uitleesbare tekst."
        except Exception as e: return f"PDF leesfout: {e}"
    else:
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            return "\n".join([p.text for p in doc.paragraphs])
        except:
            try: return content.decode('utf-8')
            except: return content.decode('latin-1', errors='ignore')

def upload_html(lead_id, filename, html):
    path = f"{lead_id}/{filename}"
    try:
        r = requests.post(f"{SUPABASE_URL}/storage/v1/object/kt_rapporten/{path}",
            headers={
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apikey": SUPABASE_KEY,
                "Content-Type": "text/html; charset=utf-8",
                "x-upsert": "true"
            },
            data=html.encode('utf-8'))
        if not r.ok:
            print(f"   ⚠️ Storage upload fout ({r.status_code}): {r.text[:80]}")
            return ""
        return f"{SUPABASE_URL}/storage/v1/object/public/kt_rapporten/{path}"
    except Exception as e:
        print(f"   ❌ Upload crash: {e}")
        return ""

# ═══════════════════════════════════════════════════════════════
# 🤖 MODULE 1: AI ANALYSE (Claude Sonnet V3.1 → JSON)
# ═══════════════════════════════════════════════════════════════

def run_ai():
    print("🤖 MODULE 1: AI Analyse starten...")
    resp = sb_get("kt_leads?status=eq.pending_ai")
    leads = resp.json() if resp.ok else []
    print(f"   Gevonden: {len(leads)} leads voor AI verwerking")

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    for lead in leads:
        lid = lead['id']
        file_url = lead.get("file_url", "")
        bedrijf = lead.get("company", f"{lead.get('first_name','')} {lead.get('last_name','')}".strip() or "Onbekend")
        
        content, perm_url = download_jotform_file(file_url, lid)
        if perm_url != file_url:
            sb_patch("kt_leads", lid, {"file_url": perm_url})
        
        vacature_text = lead.get("raw_vacancy_text", "")
        if not vacature_text and content:
            vacature_text = extract_text(content, perm_url)
        
        if not vacature_text:
            print(f"   ⚠️ Geen vacaturetekst voor {lid}")
            sb_patch("kt_leads", lid, {"status": "failed_ai: no text"})
            continue

        print(f"   🔄 Analyseren: {bedrijf}...")
        prompt = PROMPT_V31.format(bedrijf=bedrijf, vacature_text=vacature_text)
        
        try:
            r = client.messages.create(
                model="claude-sonnet-4-20250514", max_tokens=6000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = r.content[0].text.strip()
            
            # Strip markdown codeblocks als ze toch voorkomen
            if raw.startswith("```"):
                raw = re.sub(r'^```(?:json)?\s*', '', raw)
                raw = re.sub(r'\s*```$', '', raw)
            
            ai_data = json.loads(raw)
            
            # ICP score
            icp = ai_data.get("icp", {})
            icp_score = icp.get("icp_score", 0)
            icp_verdict = icp.get("verdict", "NURTURE_ONLY")
            status = "qualified" if icp_score >= ICP_THRESHOLD else "nurture_only"

            # Optie B: bedrijfsnaam uit AI extraheren
            ai_bedrijf = ai_data.get("vacancy", {}).get("bedrijf_naam", "").strip()
            if ai_bedrijf and ai_bedrijf.lower() not in ("onbekend", "unknown", ""):
                bedrijf = ai_bedrijf  # gebruik AI-versie voor verdere verwerking

            sb_patch("kt_leads", lid, {
                "status": status,
                "company": bedrijf,
                "raw_vacancy_text": vacature_text,
                "enhanced_vacancy_text": json.dumps(ai_data.get("storytelling", {})),
                "vacancy_report": json.dumps(ai_data),
                "icp_score": icp_score,
                "icp_verdict": icp_verdict
            })
            print(f"   ✅ {bedrijf}: Score {ai_data['header']['score']}/10, ICP {icp_score} → {status}")
        
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parse error voor {lid}: {e}")
            print(f"      Raw output start: {raw[:200]}")
            sb_patch("kt_leads", lid, {"status": f"failed_ai: json_parse"})
        except Exception as e:
            print(f"   ❌ AI fout voor {lid}: {e}")
            sb_patch("kt_leads", lid, {"status": f"failed_ai: {str(e)[:100]}"})

# ═══════════════════════════════════════════════════════════════
# 📄 MODULE 2: RAPPORT GENERATIE + EMAIL
# ═══════════════════════════════════════════════════════════════

def run_reports_and_email():
    """
    MODULE 2: Rapport genereren + uploaden naar Supabase Storage.
    Stuurt GEEN email — Lemlist (Module 4) bezorgt het rapport + vacaturetekst.
    Bevestigingsmail gaat direct via Resend vanuit de Jotform webhook.

    Status flow: qualified / nurture_only → rapport_ready
    24-uurs gate: Echt gebruikers wachten 24u. Test-adressen (wouter/test/warts) gaan direct.
    """
    print("\n📄 MODULE 2: Rapport generatie (geen Resend — Lemlist bezorgt)...")
    import datetime as dt_module

    for status in ["qualified", "nurture_only"]:
        resp = sb_get(f"kt_leads?status=eq.{status}")
        leads = resp.json() if resp.ok else []
        print(f"   Gevonden: {len(leads)} leads met status '{status}'")

        for lead in leads:
            lid = lead['id']
            email = lead.get("email", "")
            if not email or '@' not in email:
                continue

            # ── 24-uurs gate (geloofwaardige 'handmatige analyse' belofte) ──────
            created_str = lead.get("created_at", "")
            if created_str:
                if "Z" in created_str:
                    created_str = created_str.replace("Z", "+00:00")
                try:
                    created_dt = dt_module.datetime.fromisoformat(created_str)
                    now_utc = dt_module.datetime.now(dt_module.timezone.utc)
                    is_test = any(kw in email.lower() for kw in ["test", "wouter", "warts"])
                    if not is_test and now_utc < created_dt + dt_module.timedelta(hours=24):
                        print(f"   ⏳ {email} — nog geen 24u oud. Skip.")
                        continue
                except Exception:
                    pass  # Bij parse-fout: verwerk gewoon
            # ────────────────────────────────────────────────────────────────────

            bedrijf  = lead.get("company", "Onbekend")
            voornaam = (lead.get("first_name", "") or "daar").split()[0]

            try:
                ai_data = json.loads(lead.get("vacancy_report", "{}"))
            except (json.JSONDecodeError, TypeError):
                ai_data = {}

            # Optie B fallback: pak bedrijfsnaam uit AI als company nog 'Onbekend' is
            if not bedrijf or bedrijf.lower() in ("onbekend", "unknown", ""):
                ai_bedrijf = ai_data.get("vacancy", {}).get("bedrijf_naam", "").strip()
                if ai_bedrijf and ai_bedrijf.lower() not in ("onbekend", "unknown", ""):
                    bedrijf = ai_bedrijf
                    sb_patch("kt_leads", lid, {"company": bedrijf})  # alsnog opslaan

            # 1. Genereer + upload V1 Executive rapport
            v1_html = build_v1_executive(voornaam, bedrijf, ai_data, lid)
            v1_url  = upload_html(lid, "rapport_executive.html", v1_html)

            # 2. Genereer + upload V2 Storytelling vacaturetekst
            v2_html = build_v2_storytelling(ai_data, bedrijf)
            v2_url  = upload_html(lid, "rapport_vacaturetekst.html", v2_html)

            # Stel publieke rapport-URL samen (via wrapper op kandidatentekort.nl)
            report_url = f"https://kandidatentekort.nl/rapport.html?id={lid}&type=executive" if v1_url else CALENDLY
            v2_public  = f"https://kandidatentekort.nl/rapport.html?id={lid}&type=storytelling"

            # Status → rapport_ready | sla beide URLs op | Lemlist Module 4 pakt dit op
            sb_patch("kt_leads", lid, {
                "status":           "rapport_ready",
                "rapport_url":      report_url,          # ← was 'report_url' (typo fix)
                "vacaturetekst_url": v2_public,
                "icp_verdict":      status  # bewaar originele ICP uitkomst voor Lemlist routing
            })
            print(f"   ✅ Rapporten klaar → rapport_ready: {email} ({status})")
            print(f"      📄 Analyse:   {report_url}")
            print(f"      📝 Vacature:  {v2_public}")

# ═══════════════════════════════════════════════════════════════
# 💼 MODULE 3: PIPEDRIVE (alleen qualified)
# ═══════════════════════════════════════════════════════════════

def run_pipedrive():
    """
    MODULE 3: Pipedrive deal aanmaken voor gekwalificeerde leads.
    Pikt rapport_ready leads op waar icp_verdict=qualified.
    Status: rapport_ready (qualified) → pipedrive_created
    Lemlist Module 4 stuurt daarna het rapport via de qualified campagne.
    """
    print("\n💼 MODULE 3: Pipedrive deals (qualified only)...")
    if not PIPEDRIVE_TOKEN:
        print("   ⚠️ Geen PIPEDRIVE_API_TOKEN, skip")
        return

    # Haal rapport_ready leads op die als qualified zijn aangemerkt
    resp = sb_get("kt_leads?status=eq.rapport_ready&icp_verdict=eq.qualified")
    leads = resp.json() if resp.ok else []
    print(f"   Gevonden: {len(leads)} qualified leads voor Pipedrive")

    for lead in leads:
        lid = lead['id']
        email = lead.get("email", "")
        bedrijf = lead.get("company", "Onbekend")
        
        try: ai_data = json.loads(lead.get("vacancy_report", "{}"))
        except: ai_data = {}
        
        score = ai_data.get("header", {}).get("score", "")
        icp_score = lead.get("icp_score", 0)
        report_url = lead.get("report_url", "")

        search = requests.get(f"{PIPEDRIVE_BASE}/persons/search",
            params={"term": email, "api_token": PIPEDRIVE_TOKEN})
        
        person_id = None
        if search.ok:
            items = search.json().get("data", {}).get("items", [])
            if items: person_id = items[0]["item"]["id"]
        
        if not person_id:
            cr = requests.post(f"{PIPEDRIVE_BASE}/persons",
                params={"api_token": PIPEDRIVE_TOKEN},
                json={"name": f"{lead.get('first_name','')} {lead.get('last_name','')}".strip(), "email": email})
            if cr.ok: person_id = cr.json().get("data", {}).get("id")

        if not person_id: continue

        deal_resp = requests.post(f"{PIPEDRIVE_BASE}/deals",
            params={"api_token": PIPEDRIVE_TOKEN},
            json={"title": f"Vacature Analyse — {bedrijf} ({score}/10)", "person_id": person_id, "value": 0, "currency": "EUR"})
        
        if deal_resp.ok:
            deal_id = deal_resp.json().get("data", {}).get("id")
            requests.post(f"{PIPEDRIVE_BASE}/notes", params={"api_token": PIPEDRIVE_TOKEN},
                json={"content": f"VACATURE ANALYSE V8\n\nScore: {score}/10\nICP: {icp_score}\nRapport: {report_url}\nSector: {ai_data.get('vacancy',{}).get('sector','')}", "deal_id": deal_id})
            sb_patch("kt_leads", lid, {"status": "pipedrive_created", "pipedrive_deal_id": str(deal_id)})
            print(f"   ✅ Deal: {bedrijf} (#{deal_id})")

# ═══════════════════════════════════════════════════════════════
# 📬 MODULE 4: LEMLIST — RAPPORT + VACATURETEKST BEZORGING
# ═══════════════════════════════════════════════════════════════

def run_lemlist():
    """
    MODULE 4: Lemlist injectie met rapport-URLs als custom variables.
    Lemlist bezorgt het rapport + verbeterde vacaturetekst (step 1 van campagne).

    Routing:
    - rapport_ready + icp_verdict=nurture_only → KT_LEMLIST_CAMPAIGN_NURTURE
    - pipedrive_created (qualified)             → KT_LEMLIST_CAMPAIGN_QUALIFIED

    Status daarna: lemlist_injected
    """
    print("\n📬 MODULE 4: Lemlist rapport-bezorging...")
    if not LEMLIST_KEY:
        print("   ⚠️ Geen LEMLIST_API_KEY, skip")
        return

    for query, campaign_id, label in [
        # Nurture: rapport_ready leads die NIET qualified zijn
        ("kt_leads?status=eq.rapport_ready&icp_verdict=eq.nurture_only", LEMLIST_CAMPAIGN_NURTURE, "Nurture"),
        # Qualified: nadat Pipedrive deal is aangemaakt
        ("kt_leads?status=eq.pipedrive_created", LEMLIST_CAMPAIGN_QUALIFIED, "Qualified"),
    ]:
        resp = sb_get(query)
        leads = resp.json() if resp.ok else []
        print(f"   [{label}] {len(leads)} leads te verwerken")

        for lead in leads:
            lid   = lead['id']
            email = lead.get("email", "")
            if not email:
                continue

            try:
                ai_data = json.loads(lead.get("vacancy_report", "{}"))
            except (json.JSONDecodeError, TypeError):
                ai_data = {}

            h  = ai_data.get("header", {})
            v  = ai_data.get("vacancy", {})
            bl = ai_data.get("blockers", {})
            qw = ai_data.get("quick_wins", {})

            # ── Rapport-URLs (worden gebruikt als {{variabelen}} in Lemlist emails) ──
            report_url_executive    = lead.get("report_url") or f"https://kandidatentekort.nl/rapport.html?id={lid}&type=executive"
            report_url_storytelling = f"https://kandidatentekort.nl/rapport.html?id={lid}&type=storytelling"

            payload = {
                "email":       email,
                "firstName":   lead.get("first_name", ""),
                "lastName":    lead.get("last_name", ""),
                "companyName": lead.get("company", ""),
                # Analyse uitkomsten
                "score":           h.get("score", ""),
                "functie_titel":   v.get("functie_titel", ""),
                "regio":           v.get("regio", ""),
                "sector":          v.get("sector", ""),
                # Blocker snippets voor Lemlist email-tekst
                "blocker_1": f"{bl.get('blocker_1_titel', '')} — {bl.get('blocker_1_oorzaak', '')}",
                "quick_win_1_voor": qw.get("quick_win_1_voor", ""),
                "quick_win_1_na":   qw.get("quick_win_1_na", ""),
                # Rapport-URLs als Lemlist custom variabelen
                "rapport_url":          report_url_executive,
                "vacaturetekst_url":     report_url_storytelling,
                # Legacy compat
                "report_url":                  report_url_executive,
                "link_naar_v2_vacature_html":   report_url_storytelling,
                "tags": [f"KT_{label.upper()}", "rapport_verstuurd"]
            }

            # Bypass Lemlist Cloudflare 1010-error
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            res = requests.post(
                f"https://api.lemlist.com/api/campaigns/{campaign_id}/leads",
                auth=("", LEMLIST_KEY),
                json=payload,
                headers=headers
            )

            if res.ok or res.status_code == 409:
                sb_patch("kt_leads", lid, {"status": "lemlist_injected"})
                print(f"   ✅ {email} → Lemlist [{label}] | rapport: {report_url_executive[-40:]}")
            else:
                print(f"   ❌ Lemlist fout ({email}): {res.text[:120]}")

# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════

def run():
    print("""
═══════════════════════════════════════════════════════════════
🚀 KANDIDATENTEKORT V8 — UNIFIED ENGINE (Template-Based)
═══════════════════════════════════════════════════════════════
   V1 Executive Rapport + V2 Storytelling Vacaturetekst
   ICP Scoring + Pipedrive Gating + Lemlist Split Nurture
   GEEN ROI analyse in leadgen output
═══════════════════════════════════════════════════════════════
    """)
    run_ai()
    run_reports_and_email()
    run_pipedrive()
    run_lemlist()
    print("\n✅ V8 Engine run voltooid.\n")

if __name__ == "__main__":
    run()
