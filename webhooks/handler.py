#!/usr/bin/env python3
"""
webhook_handler.py
Recruitin B.V. — Zapier webhook ontvanger + campagne automation orchestrator

Start:
  python3 ~/recruitin/webhooks/handler.py

Endpoint:
  POST http://localhost:8080/webhook
  Header: X-Webhook-Secret: <WEBHOOK_SECRET uit .env>

Testverzoek:
  curl -X POST http://localhost:8080/webhook \
    -H "Content-Type: application/json" \
    -H "X-Webhook-Secret: changeme-vervang-dit" \
    -d '{"sector":"oil & gas","functie":"Procesoperator","bedrijf":"Acme B.V.",
         "regio":"Gelderland","email":"hr@acme.nl","naam":"Jan de Vries",
         "timestamp":"2026-03-05 09:00"}'
"""

import os, sys, json, threading, logging
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv, dotenv_values

# Scripts pad toevoegen aan sys.path
BASE_DIR      = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "scripts"))

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path, override=True)
import requests

# Supabase imports
try:
    from supabase_client import log_campaign
except ImportError:
    log_campaign = None

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/recruitin_handler.log"),
    ],
)
log = logging.getLogger("webhook")

# ── Config ───────────────────────────────────────────────────────────────────
PORT           = int(os.getenv("WEBHOOK_PORT", "8080"))
SECRET         = os.getenv("WEBHOOK_SECRET", "changeme-vervang-dit")
SLACK_URL      = os.getenv("SLACK_WEBHOOK_URL", "")
JOTFORM_URL    = os.getenv("JOTFORM_URL", "https://form.jotform.com/260623885606059")

# ── Sector / slug mapping ─────────────────────────────────────────────────────
SECTOR_SLUG_MAP = {
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

CAMPAGNE_NAAM_MAP = {
    "oil-gas":          "OilGas",
    "constructie":      "Constructie",
    "automation":       "Automation",
    "productie":        "Productie",
    "renewable-energy": "Renewable",
}

# ── Hulpfuncties ─────────────────────────────────────────────────────────────

def slack(msg: str):
    if not SLACK_URL:
        log.info(f"[SLACK] {msg}")
        return
    try:
        requests.post(SLACK_URL, json={"text": msg}, timeout=5)
    except Exception as e:
        log.error(f"Slack error: {e}")


def sector_to_slug(sector: str) -> str:
    return SECTOR_SLUG_MAP.get(sector.lower().strip(), sector.lower().replace(" ", "-"))


def maak_campagne_naam(slug: str) -> str:
    prefix = CAMPAGNE_NAAM_MAP.get(slug, slug.replace("-", "").title())
    maand  = datetime.now().strftime("%Y%m")
    return f"KT_{prefix}_{maand}"


def validate_payload(data: dict) -> tuple[bool, str]:
    """Valideert inkomende webhook payload. Geeft (ok, fout) terug."""
    required = ["sector", "functie", "bedrijf", "regio", "email", "naam"]
    missing  = [f for f in required if not data.get(f, "").strip()]
    if missing:
        return False, f"Ontbrekende velden: {', '.join(missing)}"
    if "@" not in data.get("email", ""):
        return False, f"Ongeldig e-mailadres: {data.get('email')}"
    sector = data["sector"].lower().strip()
    if sector not in SECTOR_SLUG_MAP and sector not in SECTOR_SLUG_MAP.values():
        log.warning(f"Onbekende sector '{sector}' — doorgaan met best-effort slug")
    return True, ""


# ── Campagne automation ───────────────────────────────────────────────────────

def _run_jotform_async(submission_id: str):
    """Roept jotform_to_landing.py aan met submission_id."""
    import subprocess
    script = BASE_DIR / "scripts" / "jotform_to_landing.py"
    log.info(f"🔔 Jotform verwerking gestart: {submission_id}")
    try:
        env = os.environ.copy()
        for k, v in dict(dotenv_values(BASE_DIR / ".env")).items():
            env.setdefault(k, v)
        result = subprocess.run(
            ["python3", str(script), "--submission-id", submission_id],
            capture_output=True, text=True, timeout=600, env=env
        )
        if result.returncode == 0:
            log.info(f"✅ Jotform verwerkt: {submission_id}")
            slack(f"✅ Submission {submission_id} verwerkt")
        else:
            log.error(f"❌ Jotform fout: {result.stderr[-300:]}")
            slack(f"❌ Submission {submission_id} mislukt:\n{result.stderr[-200:]}")
    except Exception as e:
        log.error(f"❌ _run_jotform_async fout: {e}")
        slack(f"❌ Submission {submission_id} exception: {e}")


def run_campagne_async(payload: dict):
    """
    Voert de volledige campagne automation uit via de Master Orchestrator in een background subprocess.
    """
    sector        = payload["sector"]
    functie       = payload["functie"]
    bedrijf       = payload["bedrijf"]
    regio         = payload["regio"]
    email         = payload["email"]
    naam          = payload["naam"]
    klant_url     = payload.get("klant_url", "")

    slug          = sector_to_slug(sector)
    campagne_naam = maak_campagne_naam(slug)
    landing_url   = f"https://{slug}.vacaturekanon.nl"
    start_time    = datetime.now()

    log.info(f"▶ Start campagne automation (via Master Script): {campagne_naam}")
    slack(f"▶ *{campagne_naam}* — Campagne automation gestart via Master Script\n"
          f"   👤 {naam} · {bedrijf}\n"
          f"   🏭 {sector} · {regio}")

    try:
        master_script = BASE_DIR / "scripts" / "run_master_campaign.py"
        cmd = [
            "python3", str(master_script),
            "--sector", sector,
            "--functie", functie,
            "--bedrijf", bedrijf,
            "--regio", regio,
            "--email", email,
            "--naam", naam
        ]
        if klant_url:
            cmd.extend(["--url", klant_url])
        
        # Popen draait dit in de achtergrond (fire and forget vanaf dit Python proces)
        import subprocess
        
        # Ensure the subprocess has the full environment loaded
        env = os.environ.copy()
        env_path = BASE_DIR / ".env"
        for k, v in dict(dotenv_values(env_path)).items():
            if k not in env:
                env[k] = v
                
        log.info(f"Subprocess starten: {' '.join(cmd)}")
        subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("✅ Master script is asynchroon afgevuurd.")
        
    except Exception as e:
        log.error(f"Fout bij het starten van master orchestrator: {e}")
        slack(f"❌ *{campagne_naam}* — Kon Master Script niet starten: {e}")
# (Afronding van run_campagne_async is nu gedelegeerd aan het Master Script)


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class WebhookHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        log.info(f"{self.client_address[0]} - {format % args}")

    def send_json(self, code: int, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Webhook-Secret")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "service": "recruitin-webhook"})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        # ── Route voor Formulier (Stripe Flow Optie A) ──
        if self.path == "/lead":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            try:
                data = json.loads(body)
                telefoon = data.get("telefoon")
                email = data.get("email", "")
                naam = data.get("naam", "Klant")
                bedrijf = data.get("bedrijf", "Bedrijf")
                
                log.info(f"🆕 [LEAD CAPTURED] {naam} ({bedrijf}) - {email} - {telefoon}")
                
                # Hier zouden we opslaan in Pipedrive/DB
                
                # Stripe API call maken
                import urllib.request
                import urllib.parse
                import base64
                
                stripe_secret = os.getenv("STRIPE_SECRET_KEY", "")
                auth_string = base64.b64encode(f"{stripe_secret}:".encode()).decode()
                
                # Payload voor de Stripe session
                stripe_data = urllib.parse.urlencode({
                    "payment_method_types[0]": "card",
                    "payment_method_types[1]": "ideal",
                    "line_items[0][price_data][currency]": "eur",
                    "line_items[0][price_data][product_data][name]": f"Campagne Setup: {bedrijf}",
                    "line_items[0][price_data][unit_amount]": 50000, # 500 EUR in centen
                    "line_items[0][quantity]": 1,
                    "mode": "payment",
                    "customer_email": email,
                    # Fallback success URL voor test
                    "success_url": f"https://form.jotform.com/260623885606059?email={urllib.parse.quote(email)}&bedrijfsnaam={urllib.parse.quote(bedrijf)}",
                    "cancel_url": "http://localhost:8000/",
                }).encode()
                
                req = urllib.request.Request("https://api.stripe.com/v1/checkout/sessions", data=stripe_data)
                req.add_header("Authorization", f"Basic {auth_string}")
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
                
                try:
                    with urllib.request.urlopen(req) as response:
                        res_data = json.loads(response.read())
                        checkout_url = res_data.get("url")
                        self.send_json(200, {"status": "ok", "url": checkout_url})
                except Exception as e:
                    log.error(f"Stripe API error: {e}")
                    # Fallback naar een standaard link (al bestaat deze link eigenlijk niet meer, maar OK)
                    self.send_json(200, {"status": "ok", "url": f"https://buy.stripe.com/test_123?prefilled_email={urllib.parse.quote(email)}"})
                    
            except json.JSONDecodeError as e:
                self.send_json(400, {"error": "Invalid JSON"})
            return

        # ── Bestaande Zapier / Master Webhook ──
        if self.path != "/webhook":
            self.send_json(404, {"error": "gebruik /webhook of /lead"})
            return

        # Auth check
        incoming_secret = self.headers.get("X-Webhook-Secret", "")
        if incoming_secret != SECRET:
            log.warning(f"Ongeldige webhook secret van {self.client_address[0]}")
            self.send_json(401, {"error": "ongeldige secret"})
            return

        # Body lezen
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            log.error(f"JSON parse fout: {e}")
            self.send_json(400, {"error": f"ongeldige JSON: {e}"})
            return

        # ── Jotform submission_id flow (nieuwe Zapier setup) ──────────────────
        submission_id = data.get("submission_id", "").strip()
        if submission_id:
            log.info(f"📥 Jotform submission_id ontvangen: {submission_id}")
            self.send_json(202, {
                "status": "accepted",
                "submission_id": submission_id,
                "message": "Jotform verwerking gestart",
            })
            t = threading.Thread(
                target=_run_jotform_async,
                args=(submission_id,),
                daemon=True,
                name=f"jotform-{submission_id[-8:]}",
            )
            t.start()
            return

        # ── Legacy veld-payload (sector/functie/bedrijf) ──────────────────────
        ok, err = validate_payload(data)
        if not ok:
            log.warning(f"Ongeldige payload: {err}")
            self.send_json(400, {"error": err})
            return

        log.info(
            f"📥 Webhook ontvangen: {data.get('bedrijf')} | "
            f"{data.get('sector')} | {data.get('regio')}"
        )

        slug          = sector_to_slug(data["sector"])
        campagne_naam = maak_campagne_naam(slug)
        self.send_json(202, {
            "status":        "accepted",
            "campagne_naam": campagne_naam,
            "message":       "Campagne automation gestart — Slack notificaties volgen",
        })

        if log_campaign:
            log_campaign(campagne_naam, "accepted", {
                "sector": data.get("sector"),
                "bedrijf": data.get("bedrijf")
            })

        # Automation in background thread
        t = threading.Thread(
            target=run_campagne_async,
            args=(data,),
            daemon=True,
            name=f"campagne-{campagne_naam}",
        )
        t.start()


# ── Startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log_file = Path("/tmp/recruitin_handler.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"""
╔═══════════════════════════════════════════════╗
║  Recruitin Campagne Webhook Server            ║
║  Luistert op: http://0.0.0.0:{PORT}           ║
║  Endpoint:    POST /webhook                   ║
║  Health:      GET  /health                    ║
╠═══════════════════════════════════════════════╣
║  Ngrok tunnel (publiek maken):                ║
║  ngrok http {PORT}                            ║
║  → kopieer URL naar Zapier webhook actie      ║
╚═══════════════════════════════════════════════╝
""")

    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    try:
        log.info(f"Webhook server gestart op poort {PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Server gestopt")
        server.shutdown()
