#!/usr/bin/env python3
"""
D&A Electric — Kling Scene Submission (API-based)
==================================================
Volledig automatisch: submit → poll → download → FFmpeg assembly

Gebruik:
  cd ~/recruitin && python3 scripts/kling_da_electric.py

Vereisten:
  pip3 install requests PyJWT python-dotenv
  ffmpeg (brew install ffmpeg)

Character image moet staan op:
  /tmp/output/da-electric-bts-2026-corrected/character_front.png
"""

import os, sys, time, json, base64, subprocess
from pathlib import Path
from datetime import datetime

# ── Auto-install ontbrekende packages ────────────────────────────────────────
def ensure_pkg(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        print(f"📦 Installeer {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure_pkg("requests")
ensure_pkg("PyJWT", "jwt")
ensure_pkg("python-dotenv", "dotenv")

import requests
import jwt as pyjwt
from dotenv import load_dotenv

# ── .env laden ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
else:
    print(f"⚠️  .env niet gevonden op {ENV_PATH}")

KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_BASE       = os.getenv("KLING_API_BASE", "https://api-singapore.klingai.com")

# ── Output paden ──────────────────────────────────────────────────────────────
OUTPUT_DIR      = Path("/tmp/output/da-electric-bts-2026-corrected")
CHARACTER_IMAGE = OUTPUT_DIR / "character_front.png"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Scenes ────────────────────────────────────────────────────────────────────
SCENES = [
    {
        "name": "scene_01",
        "prompt": (
            "Documentary engineer arriving at electric motor testing station in Dutch electrical "
            "engineering facility. Navy work jacket with D&A logo visible, dark work shirt. Workshop "
            "background with electric motors on benches, switchgear control panels, testing equipment. "
            "Morning shift arrival moment, natural confident posture. Documentary photography, authentic "
            "manufacturing setting, hyperrealistic 8K. Slight subtle pan following his path. Natural "
            "facility lighting. Smooth understated movement, authentic workplace moment. No artificial staging."
        ),
    },
    {
        "name": "scene_02",
        "prompt": (
            "Close-up documentary interview in electrical engineering facility. D&A Electric engineer "
            "stands at electric motor testing workbench explaining drive systems and electrical control "
            "principles. Natural engaged hand gestures toward testing equipment and motors. Technical "
            "confidence visible. Colleague at edge of frame visible with smartphone filming. Workshop "
            "facility background with electric motors and switchgear control panels. Natural overhead "
            "workshop lighting. Documentary interview photography, hyperrealistic 8K. Subtle slow zoom "
            "into 85mm portrait lens effect. Smooth natural movement, no artificial staging."
        ),
    },
    {
        "name": "scene_03",
        "prompt": (
            "Documentary close-up focused on hands-on technical work. Testing and examining electric "
            "motor on testing workbench with precision. Adjusting control settings on switchgear control "
            "panel. Concentration visible on face. Colleague visible softly in background working with "
            "drive systems equipment. Natural workshop lighting illuminating the technical work area. "
            "Documentary technical photography, depth of field, hyperrealistic 8K, authentic engineering "
            "moment. Subtle camera movement. No artificial staging."
        ),
    },
    {
        "name": "scene_04",
        "prompt": (
            "Documentary workshop moment. Two engineers in natural collaborative discussion. Examining "
            "electric motor or control panel together. Natural conversation body language and gestures. "
            "Genuine focused engagement on technical challenge or test results. Workshop environment with "
            "electric motors and switchgear visible. Natural ambient facility lighting. Subtle camera "
            "movement observing the discussion. Documentary conversation photography, hyperrealistic 8K, "
            "no posed interaction, genuine technical discussion captured naturally."
        ),
    },
]

DURATION      = 5        # seconden per clip
ASPECT_RATIO  = "9:16"   # 1080×1920 vertical
MODEL         = "kling-v1-6"
POLL_INTERVAL = 20       # seconden tussen polls
POLL_TIMEOUT  = 900      # max 15 min per scene
STATE_FILE    = OUTPUT_DIR / "kling_state.json"

# ── Auth ──────────────────────────────────────────────────────────────────────
def make_jwt() -> str:
    now = int(time.time())
    payload = {"iss": KLING_ACCESS_KEY, "exp": now + 1800, "nbf": now - 5}
    return pyjwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256")

def api_headers() -> dict:
    return {"Authorization": f"Bearer {make_jwt()}", "Content-Type": "application/json"}

# ── State ─────────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ── API functies ──────────────────────────────────────────────────────────────
def img_to_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def submit_scene(scene: dict, max_retries: int = 5) -> str | None:
    """Dient scene in bij Kling API. Geeft task_id terug. Retry bij 429."""
    print(f"\n   📤 Submit {scene['name']}...")

    if not CHARACTER_IMAGE.exists():
        print(f"   ❌ Afbeelding ontbreekt: {CHARACTER_IMAGE}")
        print(f"      Zet character_front.png in {OUTPUT_DIR} en herstart.")
        return None

    payload = {
        "model_name":   MODEL,
        "image":        img_to_base64(CHARACTER_IMAGE),
        "prompt":       scene["prompt"],
        "duration":     DURATION,
        "aspect_ratio": ASPECT_RATIO,
        "cfg_scale":    0.5,
        "mode":         "std",
    }

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(
                f"{KLING_BASE}/v1/videos/image2video",
                headers=api_headers(),
                json=payload,
                timeout=30,
            )
            result = r.json()

            # 429 = te veel parallelle tasks — wacht en probeer opnieuw
            if r.status_code == 429 or result.get("code") == 1303:
                wait = 60 * attempt
                print(f"   ⏳ Rate limit (429) — wacht {wait}s (poging {attempt}/{max_retries})...")
                time.sleep(wait)
                continue

            task_id = (
                result.get("data", {}).get("task_id")
                or result.get("task_id")
            )
            if task_id:
                print(f"   ✅ Ingediend — task_id: {task_id}")
                return task_id
            else:
                print(f"   ❌ Submit fout (HTTP {r.status_code}):")
                print(f"      {json.dumps(result, indent=2)}")
                return None
        except Exception as e:
            print(f"   ❌ Request fout: {e}")
            if attempt < max_retries:
                time.sleep(15)

    print(f"   ❌ {scene['name']}: max retries bereikt")
    return None


def poll_scene(task_id: str, scene_name: str) -> str | None:
    """Poll totdat video klaar is. Geeft download-URL terug."""
    print(f"   ⏳ Wachten op {scene_name} (max {POLL_TIMEOUT//60} min)...")
    start = time.time()

    while time.time() - start < POLL_TIMEOUT:
        try:
            r = requests.get(
                f"{KLING_BASE}/v1/videos/image2video/{task_id}",
                headers=api_headers(),
                timeout=15,
            )
            data   = r.json().get("data", {})
            status = data.get("task_status", "unknown")
            elapsed = int(time.time() - start)
            print(f"   [{elapsed:3d}s] {scene_name}: {status}", flush=True)

            if status == "succeed":
                videos = data.get("task_result", {}).get("videos", [])
                if videos:
                    url = videos[0].get("url")
                    print(f"   ✅ Klaar!")
                    return url
                print("   ❌ Geen video URL in response")
                return None

            elif status in ("failed", "error"):
                reason = data.get("task_status_msg", "onbekend")
                print(f"   ❌ Mislukt: {reason}")
                return None

        except Exception as e:
            print(f"   ⚠️  Poll fout: {e}")

        time.sleep(POLL_INTERVAL)

    print(f"   ❌ Timeout na {POLL_TIMEOUT}s")
    return None


def download_video(url: str, dest: Path) -> bool:
    """Download video van URL naar lokaal bestand."""
    print(f"   💾 Download {dest.name}...", end="", flush=True)
    try:
        r = requests.get(url, timeout=120, stream=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        size_mb = dest.stat().st_size / 1_000_000
        print(f" {size_mb:.1f} MB ✅")
        return True
    except Exception as e:
        print(f"\n   ❌ Download fout: {e}")
        return False


def assemble_video() -> bool:
    """Assembleert 4 scenes tot 1 finale video via FFmpeg."""
    print("\n🎬 FINALE VIDEO SAMENSTELLEN...")

    missing = []
    for i in range(1, 5):
        f = OUTPUT_DIR / f"scene_{i:02d}.mp4"
        if not f.exists() or f.stat().st_size < 10_000:
            missing.append(f.name)

    if missing:
        print(f"   ❌ Ontbrekend: {', '.join(missing)}")
        return False

    concat_file = OUTPUT_DIR / "concat_final.txt"
    with open(concat_file, "w") as f:
        for i in range(1, 5):
            f.write(f"file 'scene_{i:02d}.mp4'\n")

    output_file = OUTPUT_DIR / "da_electric_bts_final.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        str(output_file),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size_mb = output_file.stat().st_size / 1_000_000
        print(f"\n{'='*70}")
        print(f"✅ FINALE VIDEO KLAAR!")
        print(f"{'='*70}")
        print(f"   📁 {output_file}")
        print(f"   📦 {size_mb:.1f} MB  |  1080×1920 (9:16)")
        return True
    else:
        print(f"   ❌ FFmpeg fout:\n{result.stderr[-600:]}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*70)
    print("D&A ELECTRIC — KLING AUTOMATISCHE VIDEO GENERATIE")
    print("="*70)
    print(f"   Start   : {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Output  : {OUTPUT_DIR}")
    print(f"   Image   : {CHARACTER_IMAGE}")
    print(f"   Model   : {MODEL}  |  {DURATION}s  |  {ASPECT_RATIO}")
    print(f"   API     : {KLING_BASE}")

    # Validatie
    if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
        print("\n❌ KLING_ACCESS_KEY of KLING_SECRET_KEY niet gevonden!")
        print(f"   Controleer: {ENV_PATH}")
        sys.exit(1)

    # JWT test
    print("\n🔐 Auth testen...")
    try:
        tok = make_jwt()
        print(f"   ✅ JWT OK ({len(tok)} chars)")
    except Exception as e:
        print(f"   ❌ JWT fout: {e}")
        sys.exit(1)

    state = load_state()
    if state:
        print(f"\n💾 Bestaande state gevonden: {list(state.keys())}")

    # ── Fase 1: Submit ────────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("FASE 1: SCENES INDIENEN")
    print("─"*70)

    for scene in SCENES:
        name = scene["name"]
        if state.get(name, {}).get("task_id"):
            existing = state[name]["task_id"]
            print(f"\n   ⏭  {name}: al ingediend ({existing})")
            continue

        task_id = submit_scene(scene)
        state.setdefault(name, {})["task_id"] = task_id
        save_state(state)

        if task_id and scene != SCENES[-1]:
            print("   ⏸  5s wachten...")
            time.sleep(5)

    # ── Fase 2: Poll + Download ───────────────────────────────────────────
    print("\n" + "─"*70)
    print("FASE 2: WACHTEN OP VIDEOS & DOWNLOADEN")
    print("─"*70)

    for i, scene in enumerate(SCENES, 1):
        name = scene["name"]
        dest = OUTPUT_DIR / f"{name}.mp4"

        if dest.exists() and dest.stat().st_size > 100_000:
            print(f"\n   ⏭  {name}: al gedownload")
            continue

        task_id = state.get(name, {}).get("task_id")
        if not task_id:
            print(f"\n   ⚠️  {name}: geen task_id — overgeslagen")
            continue

        print(f"\n📹 Scene {i}/4 — {name}")
        url = poll_scene(task_id, name)
        if url:
            state[name]["url"] = url
            save_state(state)
            download_video(url, dest)
        else:
            print(f"   ❌ {name} niet beschikbaar")

    # ── Fase 3: Assemble ──────────────────────────────────────────────────
    print("\n" + "─"*70)
    print("FASE 3: ASSEMBLY")
    print("─"*70)
    assemble_video()

    print(f"\n🏁 Klaar om {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == "__main__":
    main()
