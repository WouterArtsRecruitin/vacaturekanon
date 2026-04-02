#!/usr/bin/env python3
"""Regenerate hero + wrong truck images for BTS v3."""
import os, time, requests
from pathlib import Path

LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY", "6fb07738-805c-4b54-9201-cc7255b6654d")
LEONARDO_BASE = "https://cloud.leonardo.ai/api/rest/v1"
HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
OUTPUT_DIR = Path(__file__).parent / "bts_bloopers"

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
    "cartoon, illustration, painting, blurry, low quality"
)

SCENES = {
    "3_hero": {
        "prompt": (
            f"Epic wide cinematic shot on a Dutch highway construction site at night. "
            f"A large asphalt paving machine fills the center of the frame, steam rising from fresh hot asphalt. "
            f"A crew of 5 workers in orange high-vis vests work around the machine under powerful flood lights. "
            f"In the foreground, {CHARACTER} walks confidently TOWARD the camera, mid-stride, "
            f"looking straight at the lens with a determined expression. "
            f"Dramatic volumetric light beams cut through steam and dust. "
            f"Wet fresh asphalt reflects the construction lights. "
            f"Low camera angle, ultra-wide lens. Night sky with subtle clouds. "
            f"Behind-the-scenes film production feel — a camera operator silhouette visible at far right edge. "
            f"9:16 portrait format, cinematic dramatic lighting, photorealistic."
        ),
    },
    "4b_wrong_truck": {
        "prompt": (
            f"Behind-the-scenes blooper on a Dutch road construction site at night. "
            f"{CHARACTER} stands in the center of frame, posed confidently for a hero shot, "
            f"looking straight at camera. He does NOT see what is behind him. "
            f"On the FAR LEFT edge of the frame, a large bright GREEN concrete mixer truck "
            f"is JUST entering the shot — only the front cab and half the mixer drum visible, "
            f"the rest still outside the frame to the left. The truck has bright white headlights on. "
            f"The truck is clearly from a different company — green cab with blue accents. "
            f"One crew member on the right side notices the truck and has a shocked amused expression. "
            f"Construction flood lights illuminate the scene. Wet muddy ground. "
            f"Cinematic 9:16 portrait format, documentary style, night scene, photorealistic."
        ),
    },
}


def generate_image(prompt, width=832, height=1472):
    payload = {
        "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
        "prompt": prompt, "negative_prompt": NEGATIVE,
        "width": width, "height": height,
        "num_images": 1, "alchemy": True,
    }
    r = requests.post(f"{LEONARDO_BASE}/generations", headers=HEADERS, json=payload, timeout=30)
    if r.status_code != 200:
        print(f"  API error {r.status_code}: {r.text[:300]}")
        return None
    gen_id = r.json().get("sdGenerationJob", {}).get("generationId")
    print(f"  Generation ID: {gen_id}")
    return gen_id


def poll(gen_id, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{LEONARDO_BASE}/generations/{gen_id}", headers=HEADERS, timeout=15)
        if r.status_code != 200:
            time.sleep(5); continue
        gen = r.json().get("generations_by_pk", {})
        status = gen.get("status")
        if status == "COMPLETE":
            images = gen.get("generated_images", [])
            return images[0].get("url") if images else None
        elif status == "FAILED":
            print(f"  FAILED"); return None
        print(f"  {status}...")
        time.sleep(5)
    return None


def download(url, path):
    r = requests.get(url, timeout=60)
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"  Saved: {path.name} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("=== Leonardo AI — BTS v3 (hero + wrong truck) ===\n")

    for name, cfg in SCENES.items():
        print(f"[{name}] Generating...")
        gen_id = generate_image(cfg["prompt"])
        if not gen_id: continue
        url = poll(gen_id)
        if not url: continue
        download(url, OUTPUT_DIR / f"{name}_v3.png")
        print()
        time.sleep(3)

    print("Done!")
