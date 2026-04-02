#!/usr/bin/env python3
"""
kling_bts_bloopers.py — Kling i2v batch voor BTS Blooper scenes.

Animeert alle 7 scene images uit bts_bloopers/ naar video clips.

Usage:
    python3 kling_bts_bloopers.py --test-auth
    python3 kling_bts_bloopers.py --dry-run
    python3 kling_bts_bloopers.py                # Submit all 7
    python3 kling_bts_bloopers.py --scene 4b_wrong_truck  # Single scene
"""
import argparse
import base64
import json
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# JWT
try:
    import jwt as pyjwt
except ImportError:
    sys.exit("PyJWT niet geinstalleerd — pip3 install PyJWT")

# ── Config ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "bts_bloopers"
VIDEOS_DIR = BASE_DIR / "videos" / "bts_bloopers_v2"

# Kling API
KLING_ACCESS_KEY = os.environ.get("KLING_ACCESS_KEY", "Aeyk3t9Re9MtTab8gG4pgfh4f3gBgQAL")
KLING_SECRET_KEY = os.environ.get("KLING_SECRET_KEY", "RkfDrMkmmfJ4knQrkt9nYGTf3GB4f3tD")
KLING_BASE = "https://api.klingai.com"

POLL_INTERVAL = 15  # seconds
POLL_TIMEOUT = 600  # 10 min max

# ── Scene motion prompts ──────────────────────────────────────────────────
# Subtle motion prompts — Kling i2v adds motion to the still image
SCENES = {
    "1_clapperboard": {
        "motion": (
            "The hand holding the clapperboard slowly lifts it up into frame, holds steady for a beat, "
            "then snaps it shut with a crisp clap. The crew member pulls the board away to the left, "
            "revealing the supervisor standing calmly behind it. He takes a breath, adjusts his vest, "
            "and gives a small nod that he is ready. Wind gently moves his jacket. "
            "Golden hour light, camera holds steady on tripod. Cinematic."
        ),
    },
    "2_interview": {
        "motion": (
            "The supervisor talks naturally to camera, calm confident hand gestures, "
            "occasionally glancing down to think then back to lens. "
            "The colleague on the right slowly raises his phone to film, smirking. "
            "Background machines idle, lights glow warm. Gentle breeze moves clothing. "
            "Camera very slow steady push-in. Documentary interview feel, natural pace."
        ),
    },
    "3_hero": {
        "motion": (
            "The supervisor walks confidently toward the camera in slow deliberate strides. "
            "Massive clouds of steam billow up behind him from the asphalt paving machine. "
            "Crew members work on both sides, shoveling and moving equipment. "
            "Volumetric light beams cut through the steam and dust. "
            "Wet asphalt reflects the flood lights. His jacket sways with each step. "
            "Camera holds low angle as he approaches. Epic cinematic slow-motion feel."
        ),
    },
    "4a_forgot_lines": {
        "motion": (
            "The supervisor starts speaking, then gradually slows down and stops. "
            "He blinks, looks slightly upward trying to recall, purses his lips. "
            "A beat of silence. Then he breaks into a quiet smile, shakes his head at himself, "
            "and casually raises one hand in a gentle stop gesture. "
            "Crew member in background notices and starts grinning. "
            "Natural subtle movement, not exaggerated. Camera holds steady, documentary feel."
        ),
    },
    "4b_wrong_truck": {
        "motion": (
            "The green truck in the background slowly drives from left to right across the frame, "
            "its headlights sweeping across the scene. The supervisor keeps posing and smiling "
            "at the camera for a few seconds, unaware. Then the rumble gets louder, "
            "he frowns slightly, slowly turns his head to look behind him. "
            "His expression changes to amused shock. The colleague on the right starts laughing. "
            "Construction flood lights illuminate everything. Camera holds perfectly steady."
        ),
    },
    "4c_director": {
        "motion": (
            "The supervisor stands behind the camera, studying the shot seriously. "
            "He slowly leans in, squints, then starts pointing and directing his colleague "
            "with increasingly confident gestures. The colleague shifts awkwardly, "
            "not knowing where to put his hands. The supervisor steps back, "
            "crosses his arms and nods approvingly like a real director. "
            "Others watch from the side with quiet grins. Warm golden light. "
            "Camera slight gentle movement."
        ),
    },
    "4d_coffee": {
        "motion": (
            "Close-up: the tilted coffee cup slowly drips the last dark drops onto the script. "
            "Each drop splashes into the growing brown stain on the paper. "
            "The paper slowly warps and buckles from the moisture. "
            "In the soft background, the figure slowly raises both hands higher in frustration. "
            "Wind gently lifts the corner of the wet page. "
            "Camera holds close, shallow depth of field, slow contemplative pace."
        ),
    },
}


def kling_jwt() -> str:
    now = int(time.time())
    payload = {"iss": KLING_ACCESS_KEY, "exp": now + 1800, "nbf": now - 5}
    return pyjwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256",
                        headers={"alg": "HS256", "typ": "JWT"})


def kling_headers() -> dict:
    return {"Authorization": f"Bearer {kling_jwt()}", "Content-Type": "application/json"}


def test_auth():
    print("Testing Kling API auth...")
    try:
        r = requests.get(f"{KLING_BASE}/v1/videos/image2video", headers=kling_headers(), timeout=10)
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.text[:200]}")
        return r.status_code != 401
    except Exception as e:
        print(f"  Error: {e}")
        return False


def submit_job(image_path: Path, motion_prompt: str, dry_run: bool = False) -> str | None:
    if dry_run:
        fake_id = f"dry-{image_path.stem}-{int(time.time())}"
        print(f"  [DRY RUN] {fake_id}")
        print(f"  Motion: {motion_prompt[:80]}...")
        return fake_id

    img_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")

    payload = {
        "model_name": "kling-v1-5",
        "image": img_b64,
        "prompt": motion_prompt,
        "duration": 10,
        "aspect_ratio": "9:16",
        "cfg_scale": 0.5,
        "mode": "pro",
    }

    try:
        r = requests.post(f"{KLING_BASE}/v1/videos/image2video",
                          headers=kling_headers(), json=payload, timeout=30)
        result = r.json()
        task_id = result.get("data", {}).get("task_id") or result.get("task_id")
        if task_id:
            print(f"  Submitted: {task_id}")
            return task_id
        else:
            print(f"  ERROR: {result}")
            return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def poll_job(task_id: str, dry_run: bool = False) -> str | None:
    if dry_run:
        return f"https://example.com/dry-run-{task_id}.mp4"

    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        try:
            r = requests.get(f"{KLING_BASE}/v1/videos/image2video/{task_id}",
                             headers=kling_headers(), timeout=15)
            data = r.json().get("data", {})
            status = data.get("task_status", "")

            if status == "succeed":
                videos = data.get("task_result", {}).get("videos", [])
                if videos:
                    return videos[0].get("url")
            elif status in ("failed", "error"):
                print(f"  FAILED: {data.get('task_status_msg', 'unknown')}")
                return None
            else:
                print(f"  {status}...")
        except Exception as e:
            print(f"  Poll error: {e}")

        time.sleep(POLL_INTERVAL)

    print(f"  TIMEOUT after {POLL_TIMEOUT}s")
    return None


def download(url: str, output_path: Path, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"  [DRY RUN] Would save to {output_path.name}")
        return True

    r = requests.get(url, timeout=120, stream=True)
    with open(output_path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Saved: {output_path.name} ({mb:.1f} MB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Kling i2v BTS Bloopers batch")
    parser.add_argument("--test-auth", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scene", choices=list(SCENES.keys()))
    args = parser.parse_args()

    if args.test_auth:
        ok = test_auth()
        sys.exit(0 if ok else 1)

    selected = {args.scene: SCENES[args.scene]} if args.scene else SCENES
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"=== Kling i2v — BTS Bloopers ({len(selected)} scenes) ===\n")

    # Phase 1: Submit all jobs (Kling kan 2-3 parallel)
    # Submit in batches of 2 to avoid resource pack limit
    jobs = {}  # scene_name -> task_id
    scene_list = list(selected.items())

    batch_size = 2
    for batch_start in range(0, len(scene_list), batch_size):
        batch = scene_list[batch_start:batch_start + batch_size]

        for name, cfg in batch:
            # Prefer v3 image if it exists
            img_path = IMAGES_DIR / f"{name}_v3.png"
            if not img_path.exists():
                img_path = IMAGES_DIR / f"{name}.png"
            if not img_path.exists():
                print(f"[{name}] SKIP — image not found: {img_path.name}")
                continue

            print(f"[{name}] Submitting...")
            task_id = submit_job(img_path, cfg["motion"], args.dry_run)
            if task_id:
                jobs[name] = task_id

        # Wait before next batch (except dry-run)
        if not args.dry_run and batch_start + batch_size < len(scene_list):
            print(f"\n  Waiting 10s before next batch...\n")
            time.sleep(10)

    if not jobs:
        print("No jobs submitted!")
        return

    # Phase 2: Poll all jobs
    print(f"\n=== Polling {len(jobs)} jobs ===\n")
    results = {}

    for name, task_id in jobs.items():
        print(f"[{name}] Polling {task_id[:16]}...")
        url = poll_job(task_id, args.dry_run)
        if url:
            output_path = VIDEOS_DIR / f"{name}.mp4"
            ok = download(url, output_path, args.dry_run)
            results[name] = "OK" if ok else "DOWNLOAD_FAILED"
        else:
            results[name] = "FAILED"
        print()

    # Summary
    print("=== Results ===")
    for name, status in results.items():
        print(f"  {name}: {status}")

    ok = sum(1 for s in results.values() if s == "OK")
    print(f"\n{ok}/{len(results)} clips generated → {VIDEOS_DIR}/")

    # Save log
    log = {
        "timestamp": datetime.now().isoformat(),
        "scenes": {n: {"task_id": jobs.get(n, ""), "status": s} for n, s in results.items()},
    }
    log_path = VIDEOS_DIR / "kling_bts_log.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"Log: {log_path.name}")


if __name__ == "__main__":
    main()
