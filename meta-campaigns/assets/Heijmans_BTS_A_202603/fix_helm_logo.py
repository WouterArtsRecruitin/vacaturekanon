#!/usr/bin/env python3
"""
fix_helm_logo.py — Plak het echte Heijmans logo (met rode dots) op de helm
in de character reference images. Auto-detecteert helm positie.

Usage:
    python3 fix_helm_logo.py              # Fix all character images
    python3 fix_helm_logo.py --preview    # Show detected positions only
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

BASE_DIR = Path(__file__).parent
FINAL_DIR = BASE_DIR / "final"
BRANDED_DIR = BASE_DIR / "branded"

# Files to process + logo scale (fraction of helm width)
HELM_CONFIGS = {
    "char-front.png": {"logo_scale": 1.3},
    "char-3quarter.png": {"logo_scale": 1.1},
    "character.png": {"logo_scale": 1.0},
}


def find_helm(image_path):
    """Auto-detect white safety helmet in image.
    Returns (center_x, center_y, width, height) of the helm front face."""
    img = np.array(Image.open(image_path).convert("RGB"))
    h, w = img.shape[:2]

    # Search only: top 35% vertically, center 70% horizontally
    y_max = int(h * 0.35)
    x_min = int(w * 0.15)
    x_max = int(w * 0.85)
    region = img[:y_max, x_min:x_max, :]

    # Strict white threshold for helmet (not sky)
    white = (
        (region[:, :, 0] > 215) &
        (region[:, :, 1] > 215) &
        (region[:, :, 2] > 215)
    )

    # Find all connected clusters
    labeled, n = ndimage.label(white)
    if n == 0:
        return None

    # Score clusters: prefer compact, large, central ones
    best_score = -1
    best_cluster = None

    for i in range(1, n + 1):
        cluster = labeled == i
        size = cluster.sum()
        if size < 500:  # too small
            continue

        rows, cols = np.where(cluster)
        cw = cols.max() - cols.min()
        ch = rows.max() - rows.min()

        if cw == 0 or ch == 0:
            continue

        # Aspect ratio: helmet is wider than tall (1.5-4x)
        aspect = cw / ch
        if aspect < 0.8 or aspect > 5:
            continue

        # Compactness: filled ratio (helmet ~40-80% filled)
        fill = size / (cw * ch)
        if fill < 0.3:
            continue

        # Score: size * compactness * centrality
        cx = int(cols.mean()) + x_min
        centrality = 1.0 - abs(cx - w / 2) / (w / 2)
        score = size * fill * centrality

        if score > best_score:
            best_score = score
            cy = int(rows.mean())
            best_cluster = (cx, cy, cw, ch)

    return best_cluster


def place_logo_on_helm(image_path, logo_path, config, output_path):
    """Auto-detect helm and place logo centered on it."""
    img = Image.open(image_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Find helmet
    helm = find_helm(image_path)
    if not helm:
        print(f"  No helmet detected in {image_path}")
        return 0, 0

    cx, cy, helm_w, helm_h = helm

    # Scale logo to fraction of helm width
    target_w = int(helm_w * config["logo_scale"])
    target_w = max(80, min(target_w, 180))  # clamp 80-180px
    ratio = target_w / logo.width
    target_h = int(logo.height * ratio)
    logo_scaled = logo.resize((target_w, target_h), Image.LANCZOS)

    # Center logo on helm front face (slightly below center)
    logo_x = cx - target_w // 2
    logo_y = cy - target_h // 2 + int(helm_h * 0.15)

    img.paste(logo_scaled, (logo_x, logo_y), logo_scaled)
    img.convert("RGB").save(output_path, quality=95)

    return target_w, target_h, logo_x, logo_y


def main():
    parser = argparse.ArgumentParser(description="Fix Heijmans helm logo")
    parser.add_argument("--preview", action="store_true", help="Show config only")
    args = parser.parse_args()

    logo_path = BRANDED_DIR / "heijmans_logo_small.png"
    if not logo_path.exists():
        print(f"Logo not found: {logo_path}")
        print("Run: python3 heijmans_logo_overlay.py --logo-only")
        return

    logo = Image.open(logo_path)
    print(f"Logo: {logo.size[0]}x{logo.size[1]}")

    if args.preview:
        print("\n=== Preview — auto-detected helm positions ===\n")
        for filename, cfg in HELM_CONFIGS.items():
            src = FINAL_DIR / filename
            if not src.exists():
                print(f"  {filename} MISSING")
                continue
            helm = find_helm(src)
            if helm:
                cx, cy, hw, hh = helm
                print(f"  {filename}")
                print(f"    Helm center: ({cx}, {cy}), size: {hw}x{hh}")
                print(f"    Logo width: {int(hw * cfg['logo_scale'])}px")
            else:
                print(f"  {filename} — no helm detected")
        return

    print("=== Fixing helm logos ===\n")

    for filename, cfg in HELM_CONFIGS.items():
        src = FINAL_DIR / filename
        if not src.exists():
            print(f"  Skipping {filename} (not found)")
            continue

        out = FINAL_DIR / filename
        result = place_logo_on_helm(src, logo_path, cfg, out)
        if len(result) == 4:
            w, h, lx, ly = result
            print(f"  {filename} — logo {w}x{h} at ({lx}, {ly})")
        else:
            print(f"  {filename} — failed")

    print(f"\nDone! Updated images in: {FINAL_DIR}/")


if __name__ == "__main__":
    main()
