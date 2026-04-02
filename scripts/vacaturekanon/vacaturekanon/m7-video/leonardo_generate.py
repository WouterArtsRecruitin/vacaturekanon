#!/usr/bin/env python3
"""
leonardo_generate.py — Genereer character + scene images via Leonardo AI (Phoenix 1.0)
========================================================================================
Stap 1 van de Vacaturekanon video pipeline.
Output: PNG images als input voor Kling image-to-video.

Gebruik:
    python3 leonardo_generate.py --test-auth
    python3 leonardo_generate.py --dry-run --sector constructie --klant "Heijmans"
    python3 leonardo_generate.py --sector constructie --klant "Heijmans" --shot char_front
    python3 leonardo_generate.py --sector automation --klant "ASML"   # alle 4 images

Output per run:
    ~/recruitin/meta-campaigns/assets/{KlantNaam}_{Sector}/
        char_front.png          ← character referentie (input voor Kling)
        scene_awareness.png     ← still voor awareness video
        scene_consideration.png ← still voor consideration video
        scene_conversion.png    ← still voor conversion video
"""

import argparse
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# ── Pad setup ─────────────────────────────────────────────────────────────────
RECRUITIN_DIR = Path.home() / "recruitin"
sys.path.insert(0, str(Path(__file__).parent))   # vacaturekanon/

from scene_prompts import get_image_prompt, list_sectors, NEGATIVE_PROMPT

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(RECRUITIN_DIR / ".env", override=True)
except ImportError:
    pass

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY", "6fb07738-805c-4b54-9201-cc7255b6654d")
LEONARDO_BASE    = "https://cloud.leonardo.ai/api/rest/v1"
PHOENIX_MODEL_ID = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"  # Phoenix 1.0

HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}

# 9:16 formaat (832×1472) voor Kling input
IMG_WIDTH  = 832
IMG_HEIGHT = 1472

SHOTS = ["char_front", "awareness", "consideration", "conversion"]
SHOT_FILENAMES = {
    "char_front":    "char_front.png",
    "awareness":     "scene_awareness.png",
    "consideration": "scene_consideration.png",
    "conversion":    "scene_conversion.png",
}

POLL_INTERVAL = 5   # sec
POLL_TIMEOUT  = 180 # sec


# ── API functies ──────────────────────────────────────────────────────────────

def test_auth() -> bool:
    print("🔑 Leonardo auth testen...")
    try:
        r = requests.get(f"{LEONARDO_BASE}/me", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            user = r.json().get("user_details", [{}])[0].get("user", {})
            name = user.get("username", "?")
            print(f"   ✅ Auth OK — gebruiker: {name}")
            return True
        else:
            print(f"   ❌ Auth mislukt ({r.status_code}): {r.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Verbindingsfout: {e}")
        return False


def generate_image(prompt: str, dry_run: bool = False) -> str | None:
    """Submit generatie naar Leonardo. Geeft generation_id terug."""
    if dry_run:
        fake_id = f"dry-{int(time.time())}"
        print(f"   [DRY RUN] generation_id: {fake_id}")
        return fake_id

    payload = {
        "modelId":         PHOENIX_MODEL_ID,
        "prompt":          prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "width":           IMG_WIDTH,
        "height":          IMG_HEIGHT,
        "num_images":      1,
        "alchemy":         True,
    }

    try:
        r = requests.post(
            f"{LEONARDO_BASE}/generations",
            headers=HEADERS, json=payload, timeout=30
        )
        if r.status_code != 200:
            print(f"   ❌ API error {r.status_code}: {r.text[:300]}")
            return None

        gen_id = r.json().get("sdGenerationJob", {}).get("generationId")
        if gen_id:
            print(f"   📋 Generation ID: {gen_id}")
            return gen_id
        else:
            print(f"   ❌ Geen generation ID: {r.json()}")
            return None

    except Exception as e:
        print(f"   ❌ Request fout: {e}")
        return None


def poll_generation(gen_id: str, dry_run: bool = False) -> str | None:
    """Poll tot image klaar is. Geeft URL terug."""
    if dry_run:
        return f"https://example.com/dry-run-{gen_id}.png"

    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        try:
            r = requests.get(
                f"{LEONARDO_BASE}/generations/{gen_id}",
                headers=HEADERS, timeout=15
            )
            if r.status_code != 200:
                time.sleep(POLL_INTERVAL)
                continue

            gen    = r.json().get("generations_by_pk", {})
            status = gen.get("status")
            print(f"   ⏳ Status: {status}...", flush=True)

            if status == "COMPLETE":
                images = gen.get("generated_images", [])
                if images:
                    return images[0].get("url")
                print("   ❌ Geen images in response")
                return None

            elif status == "FAILED":
                print("   ❌ Generatie mislukt")
                return None

        except Exception as e:
            print(f"   ⚠️  Poll fout: {e}")

        time.sleep(POLL_INTERVAL)

    print(f"   ❌ Timeout na {POLL_TIMEOUT}s")
    return None


def download_image(url: str, output_path: Path, dry_run: bool = False) -> bool:
    """Download gegenereerde image naar bestand."""
    if dry_run:
        output_path.write_bytes(b"DRY RUN PLACEHOLDER")
        print(f"   [DRY RUN] Opgeslagen: {output_path.name}")
        return True

    try:
        r = requests.get(url, timeout=60)
        with open(output_path, "wb") as f:
            f.write(r.content)
        kb = output_path.stat().st_size // 1024
        print(f"   💾 {output_path.name} ({kb} KB)")
        return True
    except Exception as e:
        print(f"   ❌ Download fout: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Leonardo AI — Vacaturekanon image generatie")
    parser.add_argument("--sector",   required=False, choices=list_sectors(),
                        default="constructie", help="Sector naam")
    parser.add_argument("--klant",    required=False, default="Vacaturekanon",
                        help="Naam van de klant (voor output folder)")
    parser.add_argument("--shot",     choices=SHOTS,
                        help="Genereer één specifieke shot")
    parser.add_argument("--test-auth", action="store_true",
                        help="Test Leonardo API authenticatie")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Preview prompts, geen API calls")
    args = parser.parse_args()

    if args.test_auth:
        ok = test_auth()
        sys.exit(0 if ok else 1)

    sector = args.sector.lower().replace(" ", "-")
    klant  = args.klant.replace(" ", "_")
    shots  = [args.shot] if args.shot else SHOTS

    # Output folder — lokaal op Mac (overschrijfbaar via RECRUITIN_OUTPUT env var)
    folder_name = f"{klant}_{sector.replace('-', '_')}"
    output_base = Path(os.getenv("RECRUITIN_OUTPUT", str(Path.home() / "Movies" / "Recruitin" / "images")))
    output_dir  = output_base / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"LEONARDO AI — {klant.upper()} / {sector.upper()}")
    print(f"{'='*70}")
    print(f"   Sector    : {sector}")
    print(f"   Klant     : {klant}")
    print(f"   Output    : {output_dir}")
    print(f"   Shots     : {shots}")
    print(f"   Formaat   : {IMG_WIDTH}×{IMG_HEIGHT} (9:16)")
    print(f"   Dry run   : {'JA' if args.dry_run else 'NEE'}")

    if not args.dry_run:
        test_auth()

    results = {}

    for shot in shots:
        filename = SHOT_FILENAMES[shot]
        output_path = output_dir / filename

        # Sla over als al bestaat
        if output_path.exists() and output_path.stat().st_size > 1000 and not args.dry_run:
            print(f"\n   ⏭  {shot}: al aanwezig ({filename})")
            results[shot] = "SKIPPED"
            continue

        print(f"\n🖼  [{shot}] Genereren...")
        prompt = get_image_prompt(sector, shot, args.klant)

        if args.dry_run:
            print(f"   PROMPT ({len(prompt)} chars):")
            print(f"   {prompt[:250]}...")

        gen_id = generate_image(prompt, args.dry_run)
        if not gen_id:
            results[shot] = "FAILED"
            continue

        url = poll_generation(gen_id, args.dry_run)
        if not url:
            results[shot] = "FAILED"
            continue

        ok = download_image(url, output_path, args.dry_run)
        results[shot] = "OK" if ok else "DOWNLOAD_FAILED"

        # Rate limit buffer
        if shot != shots[-1]:
            time.sleep(2)

    # Samenvatting
    print(f"\n{'='*70}")
    print("RESULTAAT")
    print(f"{'='*70}")
    for shot, status in results.items():
        icon = "✅" if status in ("OK", "SKIPPED") else "❌"
        print(f"   {icon} {shot}: {status}")

    ok_count = sum(1 for s in results.values() if s in ("OK", "SKIPPED"))
    print(f"\n{ok_count}/{len(results)} images gereed → {output_dir}/")

    if ok_count > 0 and not args.dry_run:
        print(f"\n▶  Volgende stap:")
        print(f"   python3 kling_vacaturekanon.py --sector {sector} --klant \"{args.klant}\"")


if __name__ == "__main__":
    main()
