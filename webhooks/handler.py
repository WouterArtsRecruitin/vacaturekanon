#!/usr/bin/env python3
"""
VACATUREKANON — Webhook Handler
Recruitin B.V. | Render deployment

Flow:
  Jotform POST → valideer → Pipedrive deal → email → Slack → spawn design agent
"""

import os
import json
import threading
import subprocess
import logging
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# ── LOGGING ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("vacaturekanon")

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET", "")
PIPEDRIVE_KEY    = os.getenv("PIPEDRIVE_API_KEY", "")
PIPEDRIVE_DOMAIN = os.getenv("PIPEDRIVE_DOMAIN", "recruitinbv")
SLACK_URL        = os.getenv("SLACK_WEBHOOK_URL", "")
ANTHROPIC_KEY    = os.getenv("ANTHROPIC_API_KEY", "")
NETLIFY_TOKEN    = os.getenv("NETLIFY_TOKEN", "")
RESEND_KEY       = os.getenv("RESEND_API_KEY", "")
KLING_ACCESS     = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET     = os.getenv("KLING_SECRET_KEY", "")

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
PORT        = int(os.getenv("PORT", 5055))

REQUIRED_FIELDS = ["functie", "bedrijf", "sector", "regio", "email", "naam"]


# ── HEALTH CHECK ─────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": "3.0",
        "service": "vacaturekanon-webhook",
        "ts": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "anthropic": bool(ANTHROPIC_KEY),
            "pipedrive":  bool(PIPEDRIVE_KEY),
            "netlify":    bool(NETLIFY_TOKEN),
            "slack":      bool(SLACK_URL),
        }
    }), 200


# ── WEBHOOK ENDPOINT ─────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    # 1. Parse payload
    try:
        if request.content_type and "json" in request.content_type:
            data = request.get_json(force=True)
        else:
            # Jotform stuurt soms form-encoded
            data = {k: v[0] if isinstance(v, list) else v for k, v in request.form.to_dict(flat=False).items()}
    except Exception as e:
        log.error(f"Payload parse fout: {e}")
        return jsonify({"ok": False, "error": "invalid_payload"}), 400

    log.info(f"Webhook ontvangen: {json.dumps(data)[:200]}")

    # 2. Valideer verplichte velden
    missing = [f for f in REQUIRED_FIELDS if not data.get(f, "").strip()]
    if missing:
        log.warning(f"Ontbrekende velden: {missing}")
        return jsonify({"ok": False, "error": "missing_fields", "fields": missing}), 422

    # 3. Campagne naam genereren
    sector_clean = data["sector"].lower().replace(" ", "-")
    campagne_naam = f"VK_{sector_clean.upper()[:10]}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    data["campagne_naam"] = campagne_naam

    log.info(f"Campagne: {campagne_naam} | {data['functie']} @ {data['bedrijf']}")

    # 4. Onmiddellijke response + async tasks
    threading.Thread(target=_run_pipeline, args=(data.copy(),), daemon=True).start()

    return jsonify({
        "ok": True,
        "campagne": campagne_naam,
        "message": f"Pipeline gestart voor {data['functie']} bij {data['bedrijf']}",
        "ts": datetime.utcnow().isoformat() + "Z"
    }), 200


# ── PIPELINE (async) ─────────────────────────────────────
def _run_pipeline(data: dict):
    """
    Volledig async pipeline:
    1. Pipedrive deal aanmaken
    2. Slack notificatie (start)
    3. Dynamic HTML genereren (Claude Sonnet)
    4. Deploy naar Netlify
    5. Slack update (live URL)
    6. Pipedrive deal updaten met URL
    """
    campagne = data.get("campagne_naam", "onbekend")
    log.info(f"[{campagne}] Pipeline gestart")

    results = {}

    # ── STAP 1: Pipedrive deal ────────────────────────────
    try:
        deal_id = _create_pipedrive_deal(data)
        results["pipedrive_deal_id"] = deal_id
        log.info(f"[{campagne}] Pipedrive deal: {deal_id}")
    except Exception as e:
        log.error(f"[{campagne}] Pipedrive fout: {e}")
        results["pipedrive_error"] = str(e)

    # ── STAP 2: Slack start notificatie ──────────────────
    _slack(f"🎯 *Vacaturekanon gestart*\n"
           f"*{data['functie']}* bij *{data['bedrijf']}*\n"
           f"Sector: {data['sector']} | {data['regio']}\n"
           f"Campagne: `{campagne}`\n"
           f"_HTML genereren..._")

    # ── STAP 3: Dynamic HTML genereren ───────────────────
    output_path = f"/tmp/{campagne}.html"
    try:
        cmd = [
            "python3", str(SCRIPTS_DIR / "generate_dynamic_landing.py"),
            "--sector",   data.get("sector", "default"),
            "--functie",  data.get("functie", ""),
            "--bedrijf",  data.get("bedrijf", ""),
            "--regio",    data.get("regio", "Nederland"),
            "--niveau",   data.get("niveau", "HBO"),
            "--urgentie", data.get("urgentie", "1-2 maanden"),
            "--fte",      str(data.get("fte", "")),
            "--salaris",  data.get("salaris", "marktconform"),
            "--output",   output_path,
            "--deploy",   # direct Netlify deploy
        ]

        if data.get("hero_image"):
            cmd.extend(["--hero-image", data["hero_image"]])

        env = {
            **dict(os.environ),
            "ANTHROPIC_API_KEY": ANTHROPIC_KEY,
            "NETLIFY_TOKEN":     NETLIFY_TOKEN,
        }

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-500:] if proc.stderr else "geen output")

        # Haal live URL uit stdout
        live_url = None
        for line in proc.stdout.split("\n"):
            if "live_url" in line.lower() and "https://" in line:
                # Zoek URL in JSON output
                pass
            if "✅ Live:" in line:
                live_url = line.split("✅ Live:")[-1].strip()

        # Probeer JSON output te parsen
        try:
            json_start = proc.stdout.rfind("{")
            json_end   = proc.stdout.rfind("}") + 1
            if json_start >= 0:
                result_json = json.loads(proc.stdout[json_start:json_end])
                live_url = result_json.get("live_url", live_url)
        except Exception:
            pass

        results["live_url"] = live_url or "URL onbekend"
        log.info(f"[{campagne}] Landing page live: {live_url}")

    except subprocess.TimeoutExpired:
        log.error(f"[{campagne}] HTML generatie timeout (>180s)")
        results["html_error"] = "timeout"
    except Exception as e:
        log.error(f"[{campagne}] HTML generatie fout: {e}")
        results["html_error"] = str(e)

    # ── STAP 4: Pipedrive updaten met URL ────────────────
    if results.get("pipedrive_deal_id") and results.get("live_url"):
        try:
            _update_pipedrive_deal(
                results["pipedrive_deal_id"],
                results["live_url"],
                campagne
            )
        except Exception as e:
            log.error(f"[{campagne}] Pipedrive update fout: {e}")

    # ── STAP 5: Slack eindresultaat ───────────────────────
    if results.get("live_url") and "http" in str(results.get("live_url", "")):
        _slack(f"✅ *Vacaturekanon LIVE*\n"
               f"*{data['functie']}* bij *{data['bedrijf']}*\n"
               f"🌐 {results['live_url']}\n"
               f"📊 Pipedrive: deal #{results.get('pipedrive_deal_id', '?')}")
    else:
        _slack(f"⚠️ *Vacaturekanon gedeeltelijk mislukt*\n"
               f"Campagne: `{campagne}`\n"
               f"Fouten: {json.dumps({k: v for k, v in results.items() if 'error' in k})}")

    log.info(f"[{campagne}] Pipeline afgerond: {json.dumps(results)}")


# ── PIPEDRIVE HELPERS ────────────────────────────────────
def _create_pipedrive_deal(data: dict) -> int:
    import requests as req

    base = f"https://{PIPEDRIVE_DOMAIN}.pipedrive.com/api/v1"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    params  = {"api_token": PIPEDRIVE_KEY}

    # Persoon aanmaken
    person_resp = req.post(f"{base}/persons", headers=headers, params=params, json={
        "name":  data.get("naam", ""),
        "email": [{"value": data.get("email", ""), "primary": True}],
    }, timeout=10)

    person_id = None
    if person_resp.status_code in (200, 201):
        person_id = person_resp.json().get("data", {}).get("id")

    # Organisatie aanmaken
    org_resp = req.post(f"{base}/organizations", headers=headers, params=params, json={
        "name": data.get("bedrijf", ""),
    }, timeout=10)

    org_id = None
    if org_resp.status_code in (200, 201):
        org_id = org_resp.json().get("data", {}).get("id")

    # Deal aanmaken
    deal_payload = {
        "title":     f"{data.get('functie')} — {data.get('bedrijf')}",
        "status":    "open",
        "pipeline_id": 15,  # Vacaturekanon pipeline
        "stage_id":    215, # Stage 1: Nieuw
        "person_id":   person_id,
        "org_id":      org_id,
    }

    deal_resp = req.post(f"{base}/deals", headers=headers, params=params, json=deal_payload, timeout=10)

    if deal_resp.status_code not in (200, 201):
        raise RuntimeError(f"Deal aanmaken mislukt: {deal_resp.text[:200]}")

    deal_id = deal_resp.json()["data"]["id"]

    # Note toevoegen
    req.post(f"{base}/notes", headers=headers, params=params, json={
        "content": f"🎯 Vacaturekanon\nFunctie: {data.get('functie')}\nSector: {data.get('sector')}\nRegio: {data.get('regio')}\nNiveau: {data.get('niveau','?')}\nUrgentie: {data.get('urgentie','?')}\nCampagne: {data.get('campagne_naam')}",
        "deal_id": deal_id,
    }, timeout=10)

    return deal_id


def _update_pipedrive_deal(deal_id: int, live_url: str, campagne: str):
    import requests as req
    base   = f"https://{PIPEDRIVE_DOMAIN}.pipedrive.com/api/v1"
    params = {"api_token": PIPEDRIVE_KEY}

    req.post(f"{base}/notes", params=params, json={
        "content": f"✅ Landing page live: {live_url}\nCampagne: {campagne}",
        "deal_id": deal_id,
    }, timeout=10)


# ── SLACK HELPER ─────────────────────────────────────────
def _slack(message: str):
    if not SLACK_URL:
        return
    try:
        import requests as req
        req.post(SLACK_URL, json={"text": message}, timeout=5)
    except Exception as e:
        log.warning(f"Slack fout: {e}")


# ── MAIN ─────────────────────────────────────────────────
if __name__ == "__main__":
    log.info(f"🚀 Vacaturekanon Webhook Handler v3.0 — poort {PORT}")
    log.info(f"   Anthropic: {'✅' if ANTHROPIC_KEY else '❌'}")
    log.info(f"   Pipedrive: {'✅' if PIPEDRIVE_KEY else '❌'}")
    log.info(f"   Netlify:   {'✅' if NETLIFY_TOKEN else '❌'}")
    log.info(f"   Slack:     {'✅' if SLACK_URL else '❌'}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
