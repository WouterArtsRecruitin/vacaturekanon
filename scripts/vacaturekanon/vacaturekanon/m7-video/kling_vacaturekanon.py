#!/usr/bin/env python3
"""
kling_vacaturekanon.py — Genereer Vacaturekanon recruitment videos via Kling API
==================================================================================
Stap 2 van de pipeline: animeer scene images naar video clips + assembleer finale video.

Gebruik:
    python3 kling_vacaturekanon.py --test-auth
    python3 kling_vacaturekanon.py --dry-run --sector constructie --klant "Heijmans"
    python3 kling_vacaturekanon.py --scene awareness --sector oil-gas --klant "Shell"
    python3 kling_vacaturekanon.py --sector automation --klant "ASML"

Volledige workflow per klant:
    1. Genereer images:   python3 leonardo_generate.py --sector [X] --klant [Y]
    2. Genereer videos:   python3 kling_vacaturekanon.py --sector [X] --klant [Y]
    3. Output:            ~/recruitin/meta-campaigns/assets/[Klant]_[sector]/videos/
                             awareness.mp4
                             consideration.mp4
                             conversion.mp4
                             vacaturekanon_[klant]_[sector]_final.mp4
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Pad setup ─────────────────────────────────────────────────────────────────
# Gebruik altijd de echte lokale ~/recruitin (niet OneDrive symlink)
RECRUITIN_DIR = Path.home() / "recruitin"
sys.path.insert(0, str(Path(__file__).parent))

from scene_prompts import get_motion_prompt, list_sectors, list_scenes

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(RECRUITIN_DIR / ".env", override=True)
except ImportError:
    pass

try:
    import jwt as pyjwt
except ImportError:
    sys.exit("❌ PyJWT niet geïnstalleerd — run: pip3 install PyJWT")

KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_BASE       = os.getenv("KLING_API_BASE", "https://api-singapore.klingai.com")

# Output lokaal op Mac — ~/Movies/Recruitin/
OUTPUT_BASE = Path(os.getenv("RECRUITIN_VIDEO_OUTPUT", str(Path.home() / "Movies" / "Recruitin" / "videos")))

DURATION      = 10      # sec per clip — PRO kwaliteit
ASPECT_RATIO  = "9:16"  # 1080×1920 vertical
MODEL         = "kling-v1-6"
MODE          = "pro"   # Heijmans kwaliteitsstandaard

POLL_INTERVAL = 20      # sec
POLL_TIMEOUT  = 900     # 15 min max per scene
BATCH_SIZE    = 2       # max 2 tegelijk (voorkomt 429)
BATCH_WAIT    = 10      # sec tussen batches

SCENES        = ["awareness", "consideration", "conversion"]

SCENE_IMAGE_MAP = {
    "awareness":     "scene_awareness.png",
    "consideration": "scene_consideration.png",
    "conversion":    "scene_conversion.png",
}


# ── Auth ──────────────────────────────────────────────────────────────────────

def make_jwt() -> str:
    now = int(time.time())
    return pyjwt.encode(
        {"iss": KLING_ACCESS_KEY, "exp": now + 1800, "nbf": now - 5},
        KLING_SECRET_KEY, algorithm="HS256"
    )

def api_headers() -> dict:
    return {"Authorization": f"Bearer {make_jwt()}", "Content-Type": "application/json"}


def test_auth() -> bool:
    print("🔑 Kling auth testen...")
    try:
        tok = make_jwt()
        import requests
        r = requests.get(
            f"{KLING_BASE}/v1/videos/image2video",
            headers=api_headers(), timeout=10
        )
        # 200 of 405 = auth OK (405 = method not allowed maar wel authenticated)
        if r.status_code in (200, 405, 404):
            print(f"   ✅ JWT OK ({len(tok)} chars) — API bereikbaar")
            return True
        elif r.status_code == 401:
            print(f"   ❌ Auth mislukt (401)")
            return False
        else:
            print(f"   ✅ JWT OK — status {r.status_code}")
            return True
    except Exception as e:
        print(f"   ❌ Fout: {e}")
        return False


# ── Kling API ─────────────────────────────────────────────────────────────────

def img_to_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def submit_scene(image_path: Path, motion_prompt: str, scene: str,
                 dry_run: bool = False, max_retries: int = 5) -> str | None:
    """Submit scene naar Kling API. Retry bij 429."""
    import requests

    if dry_run:
        fake_id = f"dry-{scene}-{int(time.time())}"
        print(f"   [DRY RUN] {fake_id}")
        print(f"   Motion: {motion_prompt[:100]}...")
        return fake_id

    if not image_path.exists():
        print(f"   ❌ Image ontbreekt: {image_path}")
        print(f"      Run eerst: python3 leonardo_generate.py --sector [sector] --klant [klant]")
        return None

    payload = {
        "model_name":   MODEL,
        "image":        img_to_base64(image_path),
        "prompt":       motion_prompt,
        "duration":     DURATION,
        "aspect_ratio": ASPECT_RATIO,
        "cfg_scale":    0.5,
        "mode":         MODE,
    }

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(
                f"{KLING_BASE}/v1/videos/image2video",
                headers=api_headers(), json=payload, timeout=30
            )
            result = r.json()

            # 429 rate limit — exponential backoff
            if r.status_code == 429 or result.get("code") == 1303:
                wait = 60 * attempt
                print(f"   ⏳ Rate limit — wacht {wait}s (poging {attempt}/{max_retries})...")
                time.sleep(wait)
                continue

            task_id = result.get("data", {}).get("task_id") or result.get("task_id")
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

    print(f"   ❌ Max retries bereikt voor {scene}")
    return None


def poll_scene(task_id: str, scene: str, dry_run: bool = False) -> str | None:
    """Poll tot video klaar is. Geeft download-URL terug."""
    import requests

    if dry_run:
        time.sleep(1)
        return f"https://example.com/dry-{scene}.mp4"

    print(f"   ⏳ Wachten op {scene} (max {POLL_TIMEOUT//60} min)...")
    start = time.time()

    while time.time() - start < POLL_TIMEOUT:
        try:
            r = requests.get(
                f"{KLING_BASE}/v1/videos/image2video/{task_id}",
                headers=api_headers(), timeout=15
            )
            data   = r.json().get("data", {})
            status = data.get("task_status", "unknown")
            print(f"   [{int(time.time()-start):3d}s] {scene}: {status}", flush=True)

            if status == "succeed":
                videos = data.get("task_result", {}).get("videos", [])
                if videos:
                    print(f"   ✅ Klaar!")
                    return videos[0].get("url")
                return None

            elif status in ("failed", "error"):
                print(f"   ❌ Mislukt: {data.get('task_status_msg', '?')}")
                return None

        except Exception as e:
            print(f"   ⚠️  Poll fout: {e}")

        time.sleep(POLL_INTERVAL)

    print(f"   ❌ Timeout")
    return None


def download_video(url: str, dest: Path, dry_run: bool = False) -> bool:
    import requests

    if dry_run:
        dest.write_bytes(b"DRY RUN")
        print(f"   [DRY RUN] {dest.name}")
        return True

    print(f"   💾 {dest.name}...", end="", flush=True)
    try:
        r = requests.get(url, timeout=120, stream=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        mb = dest.stat().st_size / 1_000_000
        print(f" {mb:.1f} MB ✅")
        return True
    except Exception as e:
        print(f"\n   ❌ Download fout: {e}")
        return False


# ── FFmpeg assembly ────────────────────────────────────────────────────────────

def assemble_video(video_dir: Path, klant: str, sector: str,
                   dry_run: bool = False) -> bool:
    print(f"\n🎬 Assembling finale video...")

    clips = [video_dir / f"{s}.mp4" for s in SCENES]
    missing = [c.name for c in clips if not c.exists() or c.stat().st_size < 10_000]

    if missing and not dry_run:
        print(f"   ❌ Ontbrekend: {', '.join(missing)}")
        return False

    concat_file  = video_dir / "concat.txt"
    output_file  = video_dir / f"vacaturekanon_{klant}_{sector}_final.mp4".replace(" ", "_")

    if not dry_run:
        with open(concat_file, "w") as f:
            for s in SCENES:
                f.write(f"file '{s}.mp4'\n")

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
        if result.returncode != 0:
            print(f"   ❌ FFmpeg fout:\n{result.stderr[-500:]}")
            return False

    mb = output_file.stat().st_size / 1_000_000 if output_file.exists() else 0
    print(f"\n{'='*70}")
    print(f"✅ FINALE VIDEO KLAAR!")
    print(f"{'='*70}")
    print(f"   📁 {output_file}")
    if not dry_run:
        print(f"   📦 {mb:.1f} MB  |  1080×1920 (9:16)")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Kling — Vacaturekanon video pipeline")
    parser.add_argument("--sector",    required=False, choices=list_sectors(),
                        default="constructie")
    parser.add_argument("--klant",     required=False, default="Vacaturekanon",
                        help="Naam klant (voor paden en bestandsnamen)")
    parser.add_argument("--scene",     choices=SCENES,
                        help="Genereer één specifieke scene")
    parser.add_argument("--test-auth", action="store_true")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Preview, geen API calls")
    parser.add_argument("--asset-dir", default=None,
                        help="Map met Leonardo images (overschrijft automatisch pad)")
    args = parser.parse_args()

    if args.test_auth:
        ok = test_auth()
        sys.exit(0 if ok else 1)

    if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
        print("❌ KLING_ACCESS_KEY of KLING_SECRET_KEY niet gevonden")
        print(f"   Controleer: {RECRUITIN_DIR}/.env")
        sys.exit(1)

    sector = args.sector.lower().replace(" ", "-")
    klant  = args.klant.replace(" ", "_")
    scenes = [args.scene] if args.scene else SCENES

    # Output folder
    folder_name = f"{klant}_{sector.replace('-', '_')}"

    # Assets (input images) — zoek in volgorde:
    if args.asset_dir:
        asset_dir = Path(args.asset_dir) / folder_name
    else:
        asset_dir = RECRUITIN_DIR / "meta-campaigns" / "assets" / folder_name
        if not asset_dir.exists():
            # Fallback 1: Leonardo output via env var
            leo_base = os.getenv("RECRUITIN_OUTPUT", "")
            if leo_base:
                asset_dir = Path(leo_base) / folder_name
        if not asset_dir.exists():
            # Fallback 2: OneDrive pad
            asset_dir = Path.home() / "Library" / "CloudStorage" / \
                        "OneDrive-Gedeeldebibliotheken-Recruitin" / \
                        "meta-campaigns" / "assets" / folder_name

    # Video output lokaal
    video_dir   = OUTPUT_BASE / folder_name
    video_dir.mkdir(parents=True, exist_ok=True)

    state_file = video_dir / "kling_state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}

    print(f"\n{'='*70}")
    print(f"KLING VACATUREKANON — {klant.upper()} / {sector.upper()}")
    print(f"{'='*70}")
    print(f"   Model     : {MODEL} | {DURATION}s | {ASPECT_RATIO} | mode={MODE}")
    print(f"   Scenes    : {scenes}")
    print(f"   Assets    : {asset_dir}")
    print(f"   Videos    : {video_dir}")
    print(f"   Dry run   : {'JA' if args.dry_run else 'NEE'}")

    if not args.dry_run:
        test_auth()

    # ── Fase 1: Submit in batches van 2 ───────────────────────────────────────
    print(f"\n{'─'*70}")
    print("FASE 1: SCENES INDIENEN")
    print(f"{'─'*70}")

    for i in range(0, len(scenes), BATCH_SIZE):
        batch = scenes[i:i + BATCH_SIZE]

        for scene in batch:
            name = scene
            if state.get(name, {}).get("task_id"):
                print(f"\n   ⏭  {name}: al ingediend ({state[name]['task_id']})")
                continue

            image_path    = asset_dir / SCENE_IMAGE_MAP[scene]
            motion_prompt = get_motion_prompt(sector, scene)

            print(f"\n📹 [{name}] Submitting...")
            print(f"   Image: {image_path.name}")

            task_id = submit_scene(image_path, motion_prompt, scene, args.dry_run)
            state.setdefault(name, {})["task_id"] = task_id
            state_file.write_text(json.dumps(state, indent=2))

        # Wacht tussen batches
        if i + BATCH_SIZE < len(scenes) and not args.dry_run:
            print(f"\n   ⏸  {BATCH_WAIT}s wachten voor volgende batch...")
            time.sleep(BATCH_WAIT)

    # ── Fase 2: Poll + Download ────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print("FASE 2: WACHTEN EN DOWNLOADEN")
    print(f"{'─'*70}")

    for scene in scenes:
        dest = video_dir / f"{scene}.mp4"

        if dest.exists() and dest.stat().st_size > 100_000:
            print(f"\n   ⏭  {scene}: al gedownload")
            continue

        task_id = state.get(scene, {}).get("task_id")
        if not task_id:
            print(f"\n   ⚠️  {scene}: geen task_id")
            continue

        print(f"\n📹 {scene}")
        url = poll_scene(task_id, scene, args.dry_run)
        if url:
            state[scene]["url"] = url
            state_file.write_text(json.dumps(state, indent=2))
            download_video(url, dest, args.dry_run)

    # ── Fase 3: Assembly ───────────────────────────────────────────────────────
    if not args.scene:
        print(f"\n{'─'*70}")
        print("FASE 3: ASSEMBLY")
        print(f"{'─'*70}")
        assemble_video(video_dir, klant, sector, args.dry_run)

    # Log
    log = {
        "timestamp": datetime.now().isoformat(),
        "klant": args.klant, "sector": sector,
        "model": MODEL, "mode": MODE, "duration": DURATION,
        "scenes": state,
    }
    log_path = video_dir / "kling_log.json"
    log_path.write_text(json.dumps(log, indent=2))

    print(f"\n🏁 Klaar om {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Log: {log_path}")

    if not args.dry_run and not args.scene:
        print(f"\n▶  Volgende stap: voeg tekst overlays toe in CapCut of DaVinci Resolve")
        print(f"   Zie: ~/recruitin/output/vacaturekanon/m7-video/video-prompts.md")


if __name__ == "__main__":
    main()
