#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║  VACATUREKANON — Jotform Formulier Aanmaken via API     ║
║                                                         ║
║  Gebruik:                                               ║
║  1. Ga naar: https://www.jotform.com/myaccount/api      ║
║  2. Kopieer je API key                                  ║
║  3. Run: python3 jotform_create_form.py --key JF_API_KEY║
╚══════════════════════════════════════════════════════════╝
"""

import json
import urllib.request
import urllib.parse
import argparse
import sys

BASE_URL = "https://api.jotform.com"


def api(key: str, method: str, path: str, data: dict = None) -> dict:
    url = f"{BASE_URL}{path}?apiKey={key}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def create_vacaturekanon_form(api_key: str) -> dict:
    print("📋 Vacaturekanon Jotform aanmaken...\n")

    # Stap 1: Leeg formulier aanmaken
    result = api(api_key, "POST", "/form", {
        "questions[1][type]": "control_head",
        "questions[1][text]": "Vacaturekanon — Vacature Intake",
        "questions[1][order]": "1",
        "questions[1][name]": "header",
    })
    form_id = result["content"]["id"]
    print(f"✅ Formulier aangemaakt! ID: {form_id}")

    # Stap 2: Alle velden definiëren
    questions = [
        # ── SECTIE 1: Bedrijf ────────────────────────────────
        {"type":"control_pagebreak","text":"Sectie 1 — Bedrijfsgegevens","name":"sectie1","order":10},
        {"type":"control_textbox","text":"Bedrijfsnaam","name":"q3_bedrijfsnaam","order":11,"required":"Yes","hint":"Volledige bedrijfsnaam"},
        {"type":"control_textbox","text":"Logo letter(s)","name":"q4_bedrijfsnaamKort","order":12,"required":"No","hint":"bijv. J (voor J de Jonge)"},
        {"type":"control_textbox","text":"Tagline / Slogan","name":"q5_tagline","order":13,"required":"No","hint":"bijv. Creating The Next-Gen Industry"},
        {"type":"control_textarea","text":"Over het bedrijf","name":"q6_overBedrijf","order":14,"required":"Yes","hint":"Beschrijf het bedrijf in 2-4 zinnen"},
        {"type":"control_textbox","text":"Website URL","name":"q7_website","order":15,"required":"No","hint":"https://..."},
        {"type":"control_dropdown","text":"Sector","name":"q8_sector","order":16,"required":"Yes",
         "options":"constructie|oil_gas|productie|automation|renewable"},
        {"type":"control_textbox","text":"Accent kleur (hex)","name":"q9_accentKleur","order":17,"required":"No","hint":"#f97316 (standaard oranje)"},
        {"type":"control_textbox","text":"Opgericht (jaar)","name":"q10_opgericht","order":18,"required":"No","hint":"bijv. 1985"},
        {"type":"control_textbox","text":"Aantal medewerkers","name":"q11_medewerkers","order":19,"required":"No","hint":"bijv. 250+"},

        # ── SECTIE 2: Vacature ───────────────────────────────
        {"type":"control_pagebreak","text":"Sectie 2 — Vacaturegegevens","name":"sectie2","order":20},
        {"type":"control_textbox","text":"Functietitel","name":"q13_functietitel","order":21,"required":"Yes","hint":"bijv. Senior Projectmanager"},
        {"type":"control_textbox","text":"Locatie","name":"q14_locatie","order":22,"required":"Yes","hint":"bijv. Rotterdam"},
        {"type":"control_dropdown","text":"Dienstverband","name":"q15_dienstverband","order":23,"required":"Yes",
         "options":"Fulltime|Parttime|ZZP/Freelance|Contract"},
        {"type":"control_textarea","text":"Hero intro tekst","name":"q16_heroIntro","order":24,"required":"No","hint":"Korte wervende tekst (1-2 zinnen)"},

        # ── SECTIE 3: Functie ────────────────────────────────
        {"type":"control_pagebreak","text":"Sectie 3 — Functieomschrijving","name":"sectie3","order":30},
        {"type":"control_textarea","text":"Taken (1 per regel)","name":"q17_taken","order":31,"required":"Yes",
         "hint":"Aansturen van teams\nKwaliteitscontrole uitvoeren\nSamenwerken met opdrachtgevers"},
        {"type":"control_textarea","text":"Eisen (1 per regel)","name":"q18_eisen","order":32,"required":"Yes",
         "hint":"5 jaar ervaring\nMBO/HBO niveau\nVCA-VOL certificaat"},

        # ── SECTIE 4: Arbeidsvoorwaarden ─────────────────────
        {"type":"control_pagebreak","text":"Sectie 4 — Arbeidsvoorwaarden","name":"sectie4","order":40},
        {"type":"control_textbox","text":"Salaris range","name":"q19_salaris","order":41,"required":"No","hint":"bijv. €3.500 - €4.500 bruto/maand"},
        {"type":"control_textarea","text":"Benefits (1 per regel: Titel: Omschrijving)","name":"q20_benefits","order":42,"required":"Yes",
         "hint":"💰 Competitief Salaris: Marktconform salaris\n🚗 Bedrijfsauto: inclusief privégebruik\n📚 Ontwikkeling: Budget voor opleidingen"},

        # ── SECTIE 5: Sollicitatie ───────────────────────────
        {"type":"control_pagebreak","text":"Sectie 5 — Sollicitatie & Contact","name":"sectie5","order":50},
        {"type":"control_email","text":"HR E-mailadres","name":"q21_hrEmail","order":51,"required":"Yes"},
        {"type":"control_textbox","text":"HR Telefoon","name":"q22_hrTelefoon","order":52,"required":"No","hint":"+31 (0)10 ..."},
        {"type":"control_textbox","text":"Careers pagina URL","name":"q23_careersUrl","order":53,"required":"No","hint":"https://bedrijf.nl/werken-bij"},
        {"type":"control_textbox","text":"Jotform sollicitatie formulier ID","name":"q24_jotformId","order":54,"required":"No","hint":"Optioneel: ID van het Jotform sollicitatieformulier"},

        # ── SECTIE 6: Statistieken ───────────────────────────
        {"type":"control_pagebreak","text":"Sectie 6 — Statistieken (optioneel)","name":"sectie6","order":60},
        {"type":"control_textbox","text":"Statistiek 1 — Waarde","name":"q25_stat1Waarde","order":61,"required":"No","hint":"bijv. 50+ of 1.200m²"},
        {"type":"control_textbox","text":"Statistiek 1 — Label","name":"q26_stat1Label","order":62,"required":"No","hint":"bijv. Projecten afgerond"},
        {"type":"control_textbox","text":"Statistiek 2 — Waarde","name":"q27_stat2Waarde","order":63,"required":"No"},
        {"type":"control_textbox","text":"Statistiek 2 — Label","name":"q28_stat2Label","order":64,"required":"No"},
        {"type":"control_textbox","text":"Statistiek 3 — Waarde","name":"q29_stat3Waarde","order":65,"required":"No"},
        {"type":"control_textbox","text":"Statistiek 3 — Label","name":"q30_stat3Label","order":66,"required":"No"},
        {"type":"control_textbox","text":"Statistiek 4 — Waarde","name":"q31_stat4Waarde","order":67,"required":"No"},
        {"type":"control_textbox","text":"Statistiek 4 — Label","name":"q32_stat4Label","order":68,"required":"No"},
    ]

    # Stap 3: Velden toevoegen
    print(f"\n📝 {len(questions)} velden toevoegen...")
    payload = {}
    for i, q in enumerate(questions, 1):
        for field, val in q.items():
            payload[f"questions[{i+1}][{field}]"] = val

    result2 = api(api_key, "PUT", f"/form/{form_id}/questions", payload)
    added = len(result2.get("content", {}))
    print(f"✅ {added} velden toegevoegd")

    # Stap 4: Formulier properties instellen
    api(api_key, "POST", f"/form/{form_id}/properties", {
        "properties[title]":          "Vacaturekanon — Vacature Intake",
        "properties[formType]":       "multipage",
        "properties[activeRedirect]": "thankYou",
        "properties[thankYouPage][0][type]": "thankYou",
        "properties[thankYouPage][0][message]": "✅ Bedankt! We genereren nu jouw vacaturelandingspagina. Je ontvangt de link zodra de pagina live is.",
        "properties[styles][btnStyle]": "simple",
        "properties[styles][colorScheme]": "f97316",
    })
    print("✅ Formulier properties ingesteld")

    # Stap 5: Resultaat
    form_url = f"https://form.jotform.com/{form_id}"
    edit_url = f"https://www.jotform.com/form-templates/{form_id}"
    webhook_info = "https://www.jotform.com/myform/{form_id}/settings → Webhooks"

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  ✅ JOTFORM FORMULIER AANGEMAAKT!                       ║
║                                                         ║
║  Form ID:  {form_id:<44} ║
║  URL:      {form_url[:44]:<44} ║
║                                                         ║
║  VOLGENDE STAP — Webhook instellen:                     ║
║  1. Ga naar: https://www.jotform.com/edit/{form_id:<13} ║
║  2. Settings → Integrations → Webhooks                  ║
║  3. Add webhook: http://JOUW-IP:5055/webhook            ║
╚══════════════════════════════════════════════════════════╝
""")

    return {
        "form_id": form_id,
        "form_url": form_url,
        "edit_url": f"https://www.jotform.com/edit/{form_id}",
        "webhook_endpoint": "http://JOUW-IP:5055/webhook",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", "-k", required=True, help="Jotform API key")
    args = parser.parse_args()

    result = create_vacaturekanon_form(args.key)
    print(json.dumps(result, indent=2))
