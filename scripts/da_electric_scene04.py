#!/usr/bin/env python3
"""Scene 4 opnieuw indienen voor D&A Electric, dan assembleren."""
import base64, json, os, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "recruitin" / "scripts" / "vacaturekanon"))
from dotenv import load_dotenv
load_dotenv(Path.home() / "recruitin" / ".env", override=True)
import jwt as pyjwt
import requests

ACCESS = os.getenv("KLING_ACCESS_KEY", "")
SECRET = os.getenv("KLING_SECRET_KEY", "")
BASE   = os.getenv("KLING_API_BASE", "https://api-singapore.klingai.com")
OUT    = Path("/tmp/output/da-electric-bts-2026-corrected")
IMG    = OUT / "character_front.png"
STATE  = OUT / "kling_state.json"

PROMPT = (
    "Documentary workshop moment. Two engineers in natural collaborative discussion. "
    "Examining electric motor or control panel together. Natural conversation body language "
    "and gestures. Genuine focused engagement on technical challenge or test results. "
    "Workshop environment with electric motors and switchgear visible. Natural ambient "
    "facility lighting. Subtle camera movement observing the discussion. Documentary "
    "conversation photography, hyperrealistic 8K, no posed interaction, genuine technical "
    "discussion captured naturally."
)

def jwt():
    now = int(time.time())
    return pyjwt.encode({"iss": ACCESS, "exp": now+1800, "nbf": now-5}, SECRET, algorithm="HS256")

def hdrs():
    return {"Authorization": f"Bearer {jwt()}", "Content-Type": "application/json"}

def submit(max_retries=6):
    with open(IMG, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    payload = {
        "model_name": "kling-v1-6", "image": img_b64, "prompt": PROMPT,
        "duration": 5, "aspect_ratio": "9:16", "cfg_scale": 0.5, "mode": "std",
    }
    for attempt in range(1, max_retries + 1):
        r = requests.post(f"{BASE}/v1/videos/image2video", headers=hdrs(), json=payload, timeout=30)
        result = r.json()
        if r.status_code == 429 or result.get("code") == 1303:
            wait = 60 * attempt
            print(f"timing Rate limit — wacht {wait}s (poging {attempt}/{max_retries})...")
            time.sleep(wait)
            continue
        task_id = result.get("data", {}).get("task_id") or result.get("task_id")
        if task_id:
            print(f"scene_04 ingediend: {task_id}")
            state = json.loads(STATE.read_text()) if STATE.exists() else {}
            state["scene_04"] = {"task_id": task_id}
            STATE.write_text(json.dumps(state, indent=2))
            return task_id
        print(f"Submit fout: {result}")
        return None
    return None

def poll(task_id):
    print("Wachten op scene_04...")
    start = time.time()
    while time.time() - start < 900:
        r = requests.get(f"{BASE}/v1/videos/image2video/{task_id}", headers=hdrs(), timeout=15)
        data   = r.json().get("data", {})
        status = data.get("task_status", "?")
        print(f"[{int(time.time()-start):3d}s] {status}", flush=True)
        if status == "succeed":
            return data.get("task_result", {}).get("videos", [{}])[0].get("url")
        elif status in ("failed", "error"):
            return None
        time.sleep(20)
    return None

def download(url):
    dest = OUT / "scene_04.mp4"
    r = requests.get(url, timeout=120, stream=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    mb = dest.stat().st_size / 1e6
    print(f"scene_04.mp4 ({mb:.1f} MB) OK")

def assemble():
    concat = OUT / "concat_final.txt"
    with open(concat, "w") as f:
        for i in range(1, 5):
            f.write(f"file 'scene_{i:02d}.mp4'\n")
    out_file = OUT / "da_electric_bts_final.mp4"
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
           "-c:v", "libx264", "-c:a", "aac", "-preset", "fast",
           "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
           str(out_file)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(OUT))
    if r.returncode == 0:
        mb = out_file.stat().st_size / 1e6
        print(f"FINALE VIDEO KLAAR: {out_file}  ({mb:.1f} MB | 1080x1920)")
    else:
        print(f"FFmpeg fout: {r.stderr[-300:]}")

print("=== D&A Electric - Scene 04 + Assembly ===")
task_id = submit()
if task_id:
    url = poll(task_id)
    if url:
        download(url)
        assemble()
    else:
        print("Scene 04 mislukt")
else:
    print("Submit mislukt")
