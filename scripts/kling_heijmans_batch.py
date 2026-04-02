#!/usr/bin/env python3
"""
kling_heijmans_batch.py — Kling i2v jobs voor Heijmans BTS v2
Model: kling-v1-5 | Mode: pro | Duration: 5s | Aspect: 9:16

Usage:
    python3 kling_heijmans_batch.py                 # Submit B1 + B2 (B3 is done)
    python3 kling_heijmans_batch.py --dry-run       # Preview prompts only
    python3 kling_heijmans_batch.py --scene B1      # Submit single scene
    python3 kling_heijmans_batch.py --all            # Submit all 3 (incl B3)
"""
import argparse
import os, sys, time, json, base64, requests
from pathlib import Path
from dotenv import load_dotenv

try:
    import jwt as pyjwt
except ImportError:
    print("pip install PyJWT"); sys.exit(1)

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path, override=True)

KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_BASE = "https://api-singapore.klingai.com"

def _validate_keys():
    if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
        print("❌ KLING_ACCESS_KEY and/or KLING_SECRET_KEY not set in .env")
        sys.exit(1)

ASSETS = Path(__file__).resolve().parents[1] / "meta-campaigns/assets/Heijmans_BTS_A_202603/final"
OUTPUT = ASSETS.parent / "videos"
OUTPUT.mkdir(parents=True, exist_ok=True)

# === SCENE DEFINITIONS (v2 — improved prompts) ===
# B3-lunch.mp4 is DONE and PERFECT — only regenerate B1 + B2
SCENES = {
    "B1": {
        "name": "B1-lunch-v4",
        "image": ASSETS / "B3-lunch.png",  # Leonardo AI reference met correcte oranje werkkleding
        "prompt": (
            "Workers in orange jackets laughing around lunch table, one raises coffee cup, "
            "sandwiches on table, natural candid conversation, colleague gestures while talking, "
            "warm overcast daylight, handheld documentary style, camera slowly pans right, "
            "authentic blue-collar lunch break moment, "
            "no text no watermarks photorealistic 4K"
        ),
    },
    "B2": {
        "name": "B2-briefing-v3",
        "image": ASSETS / "B2-briefing.png",
        "prompt": (
            "Construction crew gathered around blueprints outdoors, senior foreman points "
            "at drawing, colleagues exchange knowing smiles, relaxed informal team dynamic "
            "with subtle humor, warm natural light, observational documentary camera "
            "gently pushes in, no text no watermarks photorealistic 4K"
        ),
    },
    "B3": {
        "name": "B3-lunch",
        "image": ASSETS / "B3-lunch.png",
        "prompt": (
            "Camera slowly pans across lunch table scene, workers eating "
            "sandwiches and drinking coffee, natural laughter and conversation, "
            "hand gestures, collegial shoulder pat, genuine candid moment, "
            "warm natural light, documentary observation style, authentic "
            "blue-collar lunch break atmosphere, "
            "no text no watermarks photorealistic 4K"
        ),
    },
}


def kling_jwt():
    now = int(time.time())
    payload = {
        "iss": KLING_ACCESS_KEY,
        "iat": now,
        "exp": now + 1800,
        "nbf": now - 5,
    }
    return pyjwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256",
                        headers={"alg": "HS256", "typ": "JWT"})


def headers():
    return {"Authorization": f"Bearer {kling_jwt()}", "Content-Type": "application/json"}


def img_b64(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        if not data:
            print(f"  ⚠️ Empty file: {path}")
            return None
        return base64.b64encode(data).decode()
    except (OSError, IOError) as e:
        print(f"  ⚠️ Could not read image {path}: {e}")
        return None


def submit(scene):
    print(f"\n🎬 Submitting {scene['name']}...")
    b64 = img_b64(scene["image"])
    if not b64:
        print(f"   ❌ Could not encode image, skipping")
        return None
    payload = {
        "model_name": "kling-v1-5",
        "image": b64,
        "prompt": scene["prompt"],
        "duration": "5",
        "aspect_ratio": "9:16",
        "cfg_scale": 0.5,
        "mode": "pro",
    }
    r = requests.post(f"{KLING_BASE}/v1/videos/image2video",
                      headers=headers(), json=payload, timeout=30)
    data = r.json()
    task_id = data.get("data", {}).get("task_id")
    if task_id:
        print(f"   ✅ Task ID: {task_id}")
        return task_id
    else:
        print(f"   ❌ Error: {data}")
        return None


def poll(task_id, name, timeout=900):
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{KLING_BASE}/v1/videos/image2video/{task_id}",
                         headers=headers(), timeout=15)
        data = r.json().get("data", {})
        status = data.get("task_status", "")
        print(f"   ⏳ {name}: {status}")

        if status == "succeed":
            videos = data.get("task_result", {}).get("videos", [])
            if videos:
                return videos[0].get("url")
        elif status in ("failed", "error"):
            print(f"   ❌ {name} failed")
            return None
        time.sleep(15)
    print(f"   ❌ Timeout for {name}")
    return None


def download(url, path):
    r = requests.get(url, timeout=120, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    mb = path.stat().st_size / 1_000_000
    print(f"   💾 {path.name} ({mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Kling Heijmans BTS batch submit")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts only")
    parser.add_argument("--scene", choices=["B1", "B2", "B3"], help="Submit single scene")
    parser.add_argument("--all", action="store_true", help="Submit all 3 (incl B3)")
    args = parser.parse_args()

    # Select scenes to process
    if args.scene:
        selected = [SCENES[args.scene]]
    elif args.all:
        selected = list(SCENES.values())
    else:
        # Default: only B1 + B2 (B3 is already done)
        selected = [SCENES["B1"], SCENES["B2"]]

    # Pre-validate all images exist
    missing = [s["name"] for s in selected if not s["image"].exists()]
    if missing:
        print(f"❌ Missing reference images: {', '.join(missing)}")
        for s in selected:
            if not s["image"].exists():
                print(f"   {s['name']}: {s['image']}")
        return

    # Dry run: just show prompts
    if args.dry_run:
        print("=== DRY RUN — Prompts preview ===\n")
        for scene in selected:
            exists = "✅" if scene["image"].exists() else "❌"
            print(f"🎬 {scene['name']}")
            print(f"   Image: {scene['image']} {exists}")
            print(f"   Prompt ({len(scene['prompt'])} chars):")
            print(f"   {scene['prompt']}\n")
        print(f"Total: {len(selected)} scenes")
        return

    _validate_keys()

    # Auth check
    print("🔑 Testing auth...")
    r = requests.get(f"{KLING_BASE}/v1/videos/image2video/test-nonexist",
                     headers=headers(), timeout=10)
    if r.status_code == 401:
        print("❌ Auth failed"); return
    print("✅ Auth OK\n")

    # Submit selected scenes
    tasks = {}
    for scene in selected:
        tid = submit(scene)
        if tid:
            tasks[scene["name"]] = tid
        time.sleep(2)  # Rate limit buffer

    if not tasks:
        print("❌ No tasks submitted"); return

    print(f"\n⏳ Polling {len(tasks)} jobs (max 15 min)...\n")

    # Poll all jobs + save log
    log = []
    for name, tid in tasks.items():
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        url = poll(tid, name)
        entry = {"scene": name, "task_id": tid, "timestamp": ts}
        if url:
            out_path = OUTPUT / f"{name}.mp4"
            download(url, out_path)
            entry.update({"status": "completed", "file": str(out_path)})
            print(f"   ✅ {name} done → {out_path}")
        else:
            entry.update({"status": "failed", "file": None})
            print(f"   ❌ {name} failed")
        log.append(entry)

    # Save log
    log_path = OUTPUT / "kling_batch_v2_log.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"\n📋 Log saved: {log_path}")
    print(f"🎬 Done! Videos in: {OUTPUT}")


if __name__ == "__main__":
    main()
