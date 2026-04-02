#!/usr/bin/env python3
"""
generate_character_leonardo.py — Genereer nieuwe character reference images
via Leonardo AI (Phoenix v2) voor Heijmans BTS campagne.

Na generatie: fix_helm_logo.py plaatst het echte logo op de helm.

Usage:
    python3 generate_character_leonardo.py              # Generate all 3
    python3 generate_character_leonardo.py --dry-run    # Preview prompts only
    python3 generate_character_leonardo.py --shot front # Single shot
"""
import argparse
import os
import time
import requests
from pathlib import Path

LEONARDO_API_KEY = "6fb07738-805c-4b54-9201-cc7255b6654d"
LEONARDO_BASE = "https://cloud.leonardo.ai/api/rest/v1"
HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

OUTPUT_DIR = Path(__file__).parent / "final"

# Heijmans Character DNA — consistent across all shots
# CORRECT: Gele helm + oranje jas (niet wit/geel-groen!)
CHARACTER_DNA = (
    "Early 40s Western European male construction foreman, short dark brown hair "
    "neatly combed, light stubble beard, strong jawline, confident approachable expression, "
    "wearing bright ORANGE high-visibility full zip jacket with grey reflective stripes, "
    "YELLOW safety hard hat, dark work trousers, "
    "muddy weathered workwear, Dutch road construction site"
)

NEGATIVE_PROMPT = (
    "text, letters, words, numbers, watermark, logo, AI artifacts, distortion, "
    "extra fingers, double limbs, plastic appearance, stock photo look, "
    "cartoon, illustration, painting, blurry, low quality"
)

# Shot definitions
SHOTS = {
    "front": {
        "filename": "char-front.png",
        "prompt": (
            f"{CHARACTER_DNA}. "
            "Standing facing camera directly, frontal portrait shot, "
            "road construction site background with yellow excavator blurred, "
            "overcast daylight, 85mm portrait lens, shallow depth of field, "
            "editorial documentary photography, hyperrealistic 8K, photorealistic"
        ),
    },
    "3quarter": {
        "filename": "char-3quarter.png",
        "prompt": (
            f"{CHARACTER_DNA}. "
            "Three-quarter view facing slightly right, natural relaxed stance, "
            "slight confident smile, road construction site with machinery blurred background, "
            "warm overcast daylight, 85mm portrait lens, soft bokeh, "
            "editorial documentary photography, hyperrealistic 8K, photorealistic"
        ),
    },
    "character": {
        "filename": "character.png",
        "prompt": (
            f"{CHARACTER_DNA}. "
            "Medium shot three-quarter view, arms relaxed at sides, "
            "looking slightly past camera with confident expression, "
            "flat Dutch polder landscape with road works in background, "
            "warm natural overcast light, 85mm lens, soft bokeh, "
            "editorial documentary photography, hyperrealistic 8K, photorealistic"
        ),
    },
}


def generate_image(prompt, negative_prompt, width=1024, height=1024):
    """Submit generation request to Leonardo AI Phoenix v2."""
    payload = {
        "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",  # Phoenix 1.0
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_images": 1,
        "alchemy": True,
    }

    r = requests.post(
        f"{LEONARDO_BASE}/generations",
        headers=HEADERS, json=payload, timeout=30
    )

    if r.status_code != 200:
        print(f"  API error {r.status_code}: {r.text[:300]}")
        return None

    data = r.json()
    gen_id = data.get("sdGenerationJob", {}).get("generationId")
    if not gen_id:
        print(f"  No generation ID returned: {data}")
        return None

    print(f"  Generation ID: {gen_id}")
    return gen_id


def poll_generation(gen_id, timeout=120):
    """Poll for generation completion."""
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(
            f"{LEONARDO_BASE}/generations/{gen_id}",
            headers=HEADERS, timeout=15
        )
        if r.status_code != 200:
            print(f"  Poll error: {r.status_code}")
            time.sleep(5)
            continue

        data = r.json()
        gen = data.get("generations_by_pk", {})
        status = gen.get("status")

        if status == "COMPLETE":
            images = gen.get("generated_images", [])
            if images:
                return images[0].get("url")
            return None
        elif status == "FAILED":
            print(f"  Generation failed")
            return None

        print(f"  Status: {status}...")
        time.sleep(5)

    print(f"  Timeout after {timeout}s")
    return None


def download_image(url, output_path):
    """Download generated image."""
    r = requests.get(url, timeout=60)
    with open(output_path, "wb") as f:
        f.write(r.content)
    kb = output_path.stat().st_size / 1000
    print(f"  Saved: {output_path.name} ({kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Leonardo AI character generation")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts only")
    parser.add_argument("--shot", choices=["front", "3quarter", "character"],
                        help="Generate single shot")
    args = parser.parse_args()

    if args.shot:
        selected = {args.shot: SHOTS[args.shot]}
    else:
        selected = SHOTS

    if args.dry_run:
        print("=== DRY RUN — Prompts ===\n")
        for name, cfg in selected.items():
            print(f"Shot: {name} → {cfg['filename']}")
            print(f"Prompt ({len(cfg['prompt'])} chars):")
            print(f"  {cfg['prompt'][:200]}...")
            print(f"Negative: {NEGATIVE_PROMPT[:100]}...")
            print()
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Leonardo AI — Heijmans Character Generation ===\n")

    for name, cfg in selected.items():
        print(f"Generating {name} ({cfg['filename']})...")

        gen_id = generate_image(cfg["prompt"], NEGATIVE_PROMPT)
        if not gen_id:
            continue

        url = poll_generation(gen_id)
        if not url:
            continue

        output_path = OUTPUT_DIR / cfg["filename"]
        download_image(url, output_path)
        print(f"  Done: {name}\n")

        time.sleep(2)  # rate limit buffer

    print("\nAll done! Now run: python3 fix_helm_logo.py")


if __name__ == "__main__":
    main()
