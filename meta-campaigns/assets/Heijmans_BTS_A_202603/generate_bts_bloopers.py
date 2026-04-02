#!/usr/bin/env python3
"""
generate_bts_bloopers.py — Genereer alle BTS blooper scene images
via Leonardo AI Phoenix voor Heijmans "Achter de Schermen" video.

7 scenes: clapperboard, interview, hero shot, 4 bloopers.

Usage:
    python3 generate_bts_bloopers.py              # Generate all
    python3 generate_bts_bloopers.py --dry-run    # Preview prompts
    python3 generate_bts_bloopers.py --scene 4a   # Single scene
"""
import argparse
import os
import time
import requests
from pathlib import Path

LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "6fb07738-805c-4b54-9201-cc7255b6654d")
LEONARDO_BASE = "https://cloud.leonardo.ai/api/rest/v1"
HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

OUTPUT_DIR = Path(__file__).parent / "bts_bloopers"

# Heijmans Character DNA
CHARACTER = (
    "Early 40s Western European male construction foreman, short dark brown hair "
    "neatly combed, light stubble beard, strong jawline, "
    "wearing bright ORANGE high-visibility full zip jacket with grey reflective stripes "
    "and small white 'Heijmans' text on chest, "
    "YELLOW safety hard hat, dark work trousers"
)

NEGATIVE = (
    "text overlay, watermark, UI elements, AI artifacts, distortion, "
    "extra fingers, double limbs, plastic appearance, stock photo look, "
    "cartoon, illustration, painting, blurry, low quality, boom microphone"
)

SCENES = {
    "1_clapperboard": {
        "prompt": (
            f"Behind-the-scenes film production on a Dutch road construction site at golden hour. "
            f"A crew member in dark clothes holds a classic black-and-white film clapperboard "
            f"directly in front of the camera, filling the lower third of the frame. "
            f"Behind the clapperboard, slightly out of focus, stands {CHARACTER}. "
            f"Warm golden hour lighting from the left. Yellow excavator and orange road barriers "
            f"blurred in background. Shot on RED camera, shallow depth of field, "
            f"cinematic 9:16 portrait composition. Photorealistic candid documentary style."
        ),
    },
    "2_interview": {
        "prompt": (
            f"Behind-the-scenes documentary interview on a Dutch highway construction site at dusk. "
            f"{CHARACTER} speaks directly to camera with natural hand gestures, "
            f"explaining something with confidence. At the edge of frame on the right, "
            f"a colleague in an orange vest holds up a smartphone filming him and grinning. "
            f"A large asphalt paving machine with warm construction lights visible behind him. "
            f"Slight lens flare from construction lighting. "
            f"Cinematic 9:16 portrait format, shallow depth of field, documentary realism. "
            f"Natural skin tones, no retouching."
        ),
    },
    "3_hero": {
        "prompt": (
            f"Epic cinematic hero shot on a Dutch highway construction site at night. "
            f"{CHARACTER} stands confidently in front of a massive illuminated asphalt "
            f"paving machine, arms slightly out, powerful stance. "
            f"His crew of 4 workers in orange vests work behind him. "
            f"Dramatic uplighting from powerful construction flood lights creates "
            f"volumetric light beams and long shadows on wet asphalt. "
            f"Steam rises from fresh asphalt. Low camera angle looking up at the supervisor. "
            f"Night sky above. Ultra-cinematic, 9:16 portrait format, dramatic lighting. "
            f"Photorealistic."
        ),
    },
    "4a_forgot_lines": {
        "prompt": (
            f"Behind-the-scenes blooper on a Dutch road construction site at golden hour. "
            f"{CHARACTER} stands in interview position but has completely forgotten his lines. "
            f"His mouth is half open, eyes looking up and to the right trying desperately to remember, "
            f"cheeks slightly puffed out, one hand raised making a 'cut' gesture, "
            f"breaking into a genuine embarrassed laugh. "
            f"Two crew members in orange vests visible in the background, one covering his mouth laughing. "
            f"Documentary candid style, 9:16 portrait, warm golden lighting. "
            f"Authentic unposed moment, slight motion blur on gesturing hand. Photorealistic."
        ),
    },
    "4b_wrong_truck": {
        "prompt": (
            f"Behind-the-scenes blooper on a Dutch road construction site at night. "
            f"{CHARACTER} stands posed for a hero shot in front of construction equipment. "
            f"Behind him, a large GREEN concrete mixer truck with bright BLUE company logo "
            f"on its side drives unexpectedly through the background of the shot. "
            f"The supervisor has turned around with a shocked and amused expression, "
            f"mouth open in disbelief, hands thrown up. "
            f"One crew member in the background is doubled over laughing. "
            f"Construction flood lights illuminate the scene dramatically. "
            f"Cinematic 9:16 portrait format, documentary style, motion blur on the truck."
        ),
    },
    "4c_director": {
        "prompt": (
            f"Behind-the-scenes blooper on a Dutch construction site at golden hour. "
            f"{CHARACTER} has taken over directing the video shoot. "
            f"He stands behind a film camera on a tripod, leaning forward intensely, "
            f"pointing aggressively with one hand at a nervous young colleague in an orange vest "
            f"who stands awkwardly in front of the camera not knowing what to do with his hands. "
            f"The supervisor is giving dramatic Hollywood director hand gestures. "
            f"Two other workers watch from the side, arms crossed, grinning. "
            f"Humorous role reversal moment. 9:16 portrait, warm lighting. Photorealistic."
        ),
    },
    "4d_coffee": {
        "prompt": (
            f"Close-up shot of a film production script printed on A4 paper on a folding "
            f"camping table at a Dutch construction site. A large brown coffee stain covers "
            f"most of the printed text, the paper is warped and wet. "
            f"A weathered hand in a dirty leather work glove holds a tilted white paper coffee cup "
            f"above the script, last brown drops falling. "
            f"In the blurred background, a figure in an orange high-vis vest has both hands "
            f"raised in frustration. Yellow hard hats and a steel thermos visible on the table. "
            f"Documentary style, shallow depth of field, 9:16 portrait format, "
            f"warm natural overcast lighting. Authentic messy work environment. Photorealistic."
        ),
    },
}


def generate_image(prompt, negative_prompt, width=832, height=1472):
    """Submit generation request to Leonardo AI Phoenix."""
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
        print(f"  No generation ID: {data}")
        return None

    print(f"  Generation ID: {gen_id}")
    return gen_id


def poll_generation(gen_id, timeout=180):
    """Poll for generation completion."""
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(
            f"{LEONARDO_BASE}/generations/{gen_id}",
            headers=HEADERS, timeout=15
        )
        if r.status_code != 200:
            time.sleep(5)
            continue

        gen = r.json().get("generations_by_pk", {})
        status = gen.get("status")

        if status == "COMPLETE":
            images = gen.get("generated_images", [])
            return images[0].get("url") if images else None
        elif status == "FAILED":
            print(f"  Generation FAILED")
            return None

        print(f"  {status}...")
        time.sleep(5)

    print(f"  Timeout after {timeout}s")
    return None


def download_image(url, output_path):
    """Download generated image."""
    r = requests.get(url, timeout=60)
    with open(output_path, "wb") as f:
        f.write(r.content)
    kb = output_path.stat().st_size / 1024
    print(f"  Saved: {output_path.name} ({kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="BTS Blooper image generation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scene", choices=list(SCENES.keys()))
    args = parser.parse_args()

    selected = {args.scene: SCENES[args.scene]} if args.scene else SCENES

    if args.dry_run:
        print("=== DRY RUN — BTS Blooper Prompts ===\n")
        for name, cfg in selected.items():
            print(f"Scene: {name}")
            print(f"Prompt ({len(cfg['prompt'])} chars):")
            print(f"  {cfg['prompt'][:150]}...")
            print()
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== Leonardo AI — Heijmans BTS Bloopers ({len(selected)} scenes) ===\n")

    results = {}
    for name, cfg in selected.items():
        print(f"[{name}] Generating...")
        gen_id = generate_image(cfg["prompt"], NEGATIVE)
        if not gen_id:
            results[name] = "FAILED"
            continue

        url = poll_generation(gen_id)
        if not url:
            results[name] = "FAILED"
            continue

        output_path = OUTPUT_DIR / f"{name}.png"
        download_image(url, output_path)
        results[name] = "OK"
        print()

        time.sleep(3)  # rate limit

    print("\n=== Results ===")
    for name, status in results.items():
        print(f"  {name}: {status}")
    ok = sum(1 for s in results.values() if s == "OK")
    print(f"\n{ok}/{len(results)} generated → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
