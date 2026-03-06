#!/usr/bin/env python3
import subprocess, sys, logging, os
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
SCRIPT_PATH    = Path(__file__).parent / "jotform_to_landing.py"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "recruitin2025")
LOG_FILE       = Path("/tmp/recruitin-local/webhook.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f: f.write(f"[{ts}] {msg}\n")

@app.route("/health")
def health():
    return {"status": "ok", "script": SCRIPT_PATH.exists()}

@app.route("/webhook/jotform", methods=["POST"])
def webhook():
    if request.headers.get("X-Webhook-Secret","") != WEBHOOK_SECRET:
        return {"error": "Unauthorized"}, 401
    data = request.get_json(silent=True) or {}
    sid = data.get("submission_id","").strip()
    if not sid: return {"error": "submission_id required"}, 400
    log(f"🔔 {sid}")
    cmd = [sys.executable, str(SCRIPT_PATH), "--submission-id", sid]
    if data.get("skip_kling"): cmd.append("--skip-kling")
    proc = subprocess.Popen(cmd, stdout=open(LOG_FILE,"a"), stderr=subprocess.STDOUT)
    log(f"🚀 PID {proc.pid}")
    return {"status": "accepted", "pid": proc.pid}, 202

if __name__ == "__main__":
    log("🌐 Webhook listener poort 5055")
    app.run(host="0.0.0.0", port=5055)
