#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   VACATUREKANON — Jotform Webhook Receiver                          ║
║   Recruitin B.V. | Automatische landing page generatie              ║
║                                                                     ║
║   Start: python3 jotform_webhook.py                                 ║
║   Poort:  5055                                                      ║
║                                                                     ║
║   Jotform Webhook URL instellen:                                    ║
║   Settings → Integrations → Webhooks → http://JOUW-IP:5055/webhook ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote_plus
from datetime import datetime
from pathlib import Path
import urllib.request
import base64

PORT = 5055
SCRIPT_DIR = Path(__file__).parent

# ── Jotform veld mapping ───────────────────────────────────────────────
# Map Jotform field names → intern JSON schema
# Pas de keys aan naar jouw Jotform veldnamen
FIELD_MAP = {
    # Bedrijf
    "q3_bedrijfsnaam":     "bedrijfsnaam",
    "q4_bedrijfsnaamKort": "bedrijfsnaam_kort",
    "q5_tagline":          "tagline",
    "q6_overBedrijf":      "over_bedrijf",
    "q7_website":          "website",
    "q8_sector":           "sector",
    "q9_accentKleur":      "accent_kleur",
    "q10_opgericht":       "opgericht",
    "q11_medewerkers":     "medewerkers",
    "q12_locaties":        "locaties",

    # Vacature
    "q13_functietitel":    "functietitel",
    "q14_locatie":         "locatie",
    "q15_dienstverband":   "dienstverband",
    "q16_heroIntro":       "hero_intro",

    # Taken & eisen (komma-gescheiden in Jotform textarea)
    "q17_taken":           "taken_raw",
    "q18_eisen":           "eisen_raw",

    # Benefits (JSON of komma-gescheiden)
    "q19_benefits":        "benefits_raw",

    # Sollicitatie
    "q20_hrEmail":         "hr_email",
    "q21_hrTelefoon":      "hr_telefoon",
    "q22_careersUrl":      "careers_url",
    "q23_jotformId":       "jotform_id",

    # Stats (optioneel)
    "q24_stat1Waarde":     "stat1_waarde",
    "q25_stat1Label":      "stat1_label",
    "q26_stat2Waarde":     "stat2_waarde",
    "q27_stat2Label":      "stat2_label",
    "q28_stat3Waarde":     "stat3_waarde",
    "q29_stat3Label":      "stat3_label",
    "q30_stat4Waarde":     "stat4_waarde",
    "q31_stat4Label":      "stat4_label",
}

SECTOR_COLORS = {
    "constructie": "#f97316",
    "oil_gas":     "#0ea5e9",
    "productie":   "#10b981",
    "automation":  "#6366f1",
    "renewable":   "#22c55e",
    "default":     "#f97316",
}


def parse_jotform_payload(raw_data: str) -> dict:
    """Verwerk Jotform POST data naar intern vacature schema"""
    fields = parse_qs(raw_data, keep_blank_values=True)
    flat = {k: unquote_plus(v[0]) for k, v in fields.items() if v}

    data = {}

    # Map bekende velden
    for jf_key, intern_key in FIELD_MAP.items():
        if jf_key in flat:
            data[intern_key] = flat[jf_key].strip()

    # Fallback: zoek op basis van veldinhoud als key niet matcht
    for key, val in flat.items():
        if "bedrijfsnaam" in key.lower() and "bedrijfsnaam" not in data:
            data["bedrijfsnaam"] = val
        if "functietitel" in key.lower() and "functietitel" not in data:
            data["functietitel"] = val
        if "sector" in key.lower() and "sector" not in data:
            data["sector"] = val
        if "email" in key.lower() and "hr_email" not in data:
            data["hr_email"] = val

    # Verwerk komma-gescheiden taken/eisen
    if "taken_raw" in data:
        data["taken"] = [t.strip() for t in data.pop("taken_raw").split("\n") if t.strip()]
    if "eisen_raw" in data:
        data["eisen"] = [e.strip() for e in data.pop("eisen_raw").split("\n") if e.strip()]

    # Verwerk stats
    stats = []
    for i in range(1, 5):
        w = data.pop(f"stat{i}_waarde", "")
        l = data.pop(f"stat{i}_label", "")
        if w and l:
            stats.append({"waarde": w, "label": l})
    if stats:
        data["stats"] = stats

    # Stel accent kleur in op basis van sector als niet opgegeven
    if "accent_kleur" not in data:
        sector = data.get("sector", "default")
        data["accent_kleur"] = SECTOR_COLORS.get(sector, "#f97316")

    # Verwerk benefits (JSON string of komma-gescheiden)
    if "benefits_raw" in data:
        raw = data.pop("benefits_raw")
        try:
            data["benefits"] = json.loads(raw)
        except json.JSONDecodeError:
            # Komma-gescheiden "Titel: Tekst" formaat
            benefits = []
            icons = ["💰","🚗","📚","🛡️","🤝","🌍","⚡","🌱"]
            for i, item in enumerate(raw.split(",")):
                item = item.strip()
                if ":" in item:
                    t, txt = item.split(":", 1)
                    benefits.append({"icon": icons[i % len(icons)], "titel": t.strip(), "tekst": txt.strip()})
                elif item:
                    benefits.append({"icon": icons[i % len(icons)], "titel": item, "tekst": ""})
            if benefits:
                data["benefits"] = benefits

    return data


def generate_page_async(vacature_data: dict):
    """Genereer landing page in background thread"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = SCRIPT_DIR / f"jotform_intake_{timestamp}.json"

    # Sla intake op
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(vacature_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  ▶ GENEREER PAGINA: {vacature_data.get('functietitel')} @ {vacature_data.get('bedrijfsnaam')}")
    print(f"  ▶ Input opgeslagen: {json_path.name}")
    print(f"{'='*60}\n")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "generate_landing_page.py"), "--input", str(json_path)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout)
        print("✅ Pagina succesvol gegenereerd!")
    else:
        print("❌ FOUT bij genereren:")
        print(result.stderr)

    # LEMLIST AUTOMATISERING: Chaser stoppen & Onboarding starten
    email = vacature_data.get("hr_email")
    if email:
        try:
            lemlist_api_key = os.environ.get("LEMLIST_API_KEY", "8fad96626dca907a8b2bb5a3e7da45d2")
            auth_str = base64.b64encode(f":{lemlist_api_key}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_str}",
                "Content-Type": "application/json"
            }
            chaser_id = "cam_rCk6CiSDa5bsradZX"
            onboarding_id = "cam_akPGRMM5jHMxxGrte"
            
            # Verwijder uit de Intake Chaser (zodat herinneringen stoppen)
            req_del = urllib.request.Request(
                f"https://api.lemlist.com/api/campaigns/{chaser_id}/leads/{email}",
                method="DELETE", headers=headers
            )
            try:
                urllib.request.urlopen(req_del)
                print(f"📧 Actie voltooid: {email} gehaald uit Intake Chaser.")
            except Exception as e:
                print(f"📧 Informatie: Lead {email} stond niet in Chaser of API error: {e}")

            # Voeg toe aan Onboarding (bevestiging + process upates)
            req_add = urllib.request.Request(
                f"https://api.lemlist.com/api/campaigns/{onboarding_id}/leads",
                data=json.dumps({"email": email, "firstName": vacature_data.get("bedrijfsnaam", "").split(" ")[0]}).encode(),
                method="POST", headers=headers
            )
            urllib.request.urlopen(req_add)
            print(f"📧 Actie voltooid: {email} succesvol toegevoegd aan Onboarding Campaign.")

        except Exception as e:
            print(f"❌ FOUT Lemlist Push in Webhook: {e}")


class WebhookHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK - Vacaturekanon Webhook Server actief")
        elif self.path == "/":
            self.send_response(200)
            self.end_headers()
            html = b"""<html><body style='font-family:sans-serif;padding:2rem'>
            <h1>Vacaturekanon Webhook Server</h1>
            <p>Status: <strong style='color:green'>Actief</strong></p>
            <p>Endpoint: <code>POST /webhook</code></p>
            <p>Health check: <a href='/health'>/health</a></p>
            </body></html>"""
            self.wfile.write(html)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path not in ("/webhook", "/webhook/"):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")

        print(f"\n[WEBHOOK] Jotform submission ontvangen ({len(raw_body)} bytes)")

        # Parse Jotform payload
        try:
            vacature_data = parse_jotform_payload(raw_body)
            print(f"  Bedrijf:  {vacature_data.get('bedrijfsnaam', '?')}")
            print(f"  Functie:  {vacature_data.get('functietitel', '?')}")
            print(f"  Sector:   {vacature_data.get('sector', '?')}")

            # Genereer pagina in background (zodat webhook snel reageert)
            thread = threading.Thread(target=generate_page_async, args=(vacature_data,))
            thread.daemon = True
            thread.start()

            # Direct 200 terugsturen aan Jotform
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "accepted",
                "message": f"Pagina wordt gegenereerd voor {vacature_data.get('bedrijfsnaam')} - {vacature_data.get('functietitel')}",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            print(f"  ❌ FOUT: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


if __name__ == "__main__":
    # Laad .env als beschikbaar
    env_file = SCRIPT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║  VACATUREKANON Webhook Server gestart        ║
║  Poort: {PORT}                                  ║
║  Endpoint: http://0.0.0.0:{PORT}/webhook       ║
║                                              ║
║  Jotform instelling:                         ║
║  Settings → Integrations → Webhooks          ║
║  URL: http://JOUW-IP:{PORT}/webhook            ║
║                                              ║
║  Ctrl+C om te stoppen                        ║
╚══════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer gestopt.")
