#!/usr/bin/env python3
"""
Heijmans Logo Generator + Image Overlay Tool

Creates the Heijmans logo as transparent PNG and overlays it on reference images.
The logo: lowercase "heijmans" in navy (#003A70) with red dots (#E31C23) above the "ij".

Usage:
    python3 heijmans_logo_overlay.py                    # Generate logo + overlay all images
    python3 heijmans_logo_overlay.py --logo-only        # Only generate logo PNG
    python3 heijmans_logo_overlay.py --endframe         # Also generate end frame
"""

import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# === HEIJMANS BRANDING ===
NAVY = (0, 58, 112)       # #003A70
RED = (227, 28, 35)       # #E31C23
YELLOW = (255, 197, 0)    # #FFC500
WHITE = (255, 255, 255)

# Font config
FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_INDEX_BOLD = 1  # Helvetica Neue Bold

def _load_font(size, index=FONT_INDEX_BOLD):
    """Load font with fallback to default if system font not found."""
    try:
        return ImageFont.truetype(FONT_PATH, size, index=index)
    except OSError:
        print(f"  ⚠️ Font not found: {FONT_PATH}, using default")
        return ImageFont.load_default()

BASE_DIR = Path(__file__).parent
FINAL_DIR = BASE_DIR / "final"
OUTPUT_DIR = BASE_DIR / "branded"


def create_heijmans_logo(size=200, bg_color=None):
    """
    Create the Heijmans logo as a PIL Image with transparent background.

    The logo is "heijmans" in navy bold + red dots above the "ij".
    Dot placement uses pixel scanning to find the font's built-in tittles
    and recolor them from navy to red — pixel-perfect at any size.
    """
    font = _load_font(size)

    # Measure text
    text = "heijmans"
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Canvas with padding
    padding = int(size * 0.1)
    canvas_w = text_w + padding * 2
    canvas_h = text_h + padding * 2

    if bg_color:
        img = Image.new("RGBA", (canvas_w, canvas_h), bg_color + (255,))
    else:
        img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)

    # Draw text in navy
    text_x = padding - bbox[0]
    text_y = padding - bbox[1]
    draw.text((text_x, text_y), text, fill=NAVY + (255,), font=font)

    # Find the "i" and "j" tittles by pixel scanning
    # Use getlength() for accurate character advance widths
    len_he = font.getlength("he")
    len_hei = font.getlength("hei")
    len_heij = font.getlength("heij")

    # X ranges where "i" and "j" characters live
    i_x_start = int(text_x + len_he)
    i_x_end = int(text_x + len_hei)
    j_x_start = int(text_x + len_hei)
    j_x_end = int(text_x + len_heij)

    # Scan for tittles: small navy pixel clusters in the top portion
    arr = np.array(img)
    navy_mask = (
        (arr[:, :, 0] < 30) &
        (arr[:, :, 1] > 30) & (arr[:, :, 1] < 90) &
        (arr[:, :, 2] > 80) &
        (arr[:, :, 3] > 200)
    )

    # For each character (i, j), find the tittle region:
    # Look in the top 40% of the character column range for a small cluster
    h = arr.shape[0]
    scan_height = int(h * 0.45)

    for x_start, x_end in [(i_x_start, i_x_end), (j_x_start, j_x_end)]:
        # Get the navy pixels in this column range, top portion only
        region = navy_mask[:scan_height, x_start:x_end]
        if not region.any():
            continue

        # Find rows with navy pixels
        row_has_navy = region.any(axis=1)
        navy_rows = np.where(row_has_navy)[0]
        if len(navy_rows) == 0:
            continue

        # The tittle is the first cluster of rows (separated by gap from stroke)
        row_diffs = np.diff(navy_rows)
        gap_idx = np.where(row_diffs > 2)[0]

        if len(gap_idx) > 0:
            # There's a gap — tittle is everything before the first gap
            tittle_end_row = navy_rows[gap_idx[0]]
        else:
            # No gap found — tittle extends to the last navy row in scan area
            tittle_end_row = navy_rows[-1]

        tittle_start_row = navy_rows[0]

        # Recolor the tittle pixels from navy to red
        for y in range(tittle_start_row, tittle_end_row + 1):
            for x in range(x_start, x_end):
                if navy_mask[y, x]:
                    arr[y, x] = [RED[0], RED[1], RED[2], arr[y, x, 3]]

    img = Image.fromarray(arr)

    # Crop to content with minimal padding
    content_bbox = img.getbbox()
    if content_bbox:
        margin = max(int(size * 0.02), 2)
        crop_box = (
            max(0, content_bbox[0] - margin),
            max(0, content_bbox[1] - margin),
            min(canvas_w, content_bbox[2] + margin),
            min(canvas_h, content_bbox[3] + margin),
        )
        img = img.crop(crop_box)

    return img


def create_endframe(width=1080, height=1920):
    """
    Create the end frame: yellow background, Heijmans logo centered,
    vacancy CTA text below.
    """
    img = Image.new("RGBA", (width, height), YELLOW + (255,))
    draw = ImageDraw.Draw(img)

    # Logo centered (larger)
    logo = create_heijmans_logo(size=120)
    logo_x = (width - logo.width) // 2
    logo_y = height // 2 - logo.height - 60
    img.paste(logo, (logo_x, logo_y), logo)

    # Vacancy title
    font_title = ImageFont.truetype(FONT_PATH, 52, index=FONT_INDEX_BOLD)
    title = "Senior Uitvoerder Wegen"
    title_bbox = font_title.getbbox(title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(
        ((width - title_w) // 2, logo_y + logo.height + 40),
        title, fill=NAVY + (255,), font=font_title
    )

    # CTA
    font_cta = ImageFont.truetype(FONT_PATH, 36, index=FONT_INDEX_BOLD)
    cta = "Kom jij ons team versterken?"
    cta_bbox = font_cta.getbbox(cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_y = logo_y + logo.height + 120
    draw.text(
        ((width - cta_w) // 2, cta_y),
        cta, fill=NAVY + (255,), font=font_cta
    )

    # "Bekijk de vacature" button
    font_btn = ImageFont.truetype(FONT_PATH, 32, index=FONT_INDEX_BOLD)
    btn_text = "Bekijk de vacature"
    btn_bbox = font_btn.getbbox(btn_text)
    btn_w = btn_bbox[2] - btn_bbox[0]
    btn_h = btn_bbox[3] - btn_bbox[1]
    btn_pad_x, btn_pad_y = 40, 20
    btn_x = (width - btn_w - btn_pad_x * 2) // 2
    btn_y = cta_y + 80

    # Button background (navy rounded rect)
    draw.rounded_rectangle(
        [btn_x, btn_y, btn_x + btn_w + btn_pad_x * 2, btn_y + btn_h + btn_pad_y * 2],
        radius=12, fill=NAVY + (255,)
    )
    draw.text(
        (btn_x + btn_pad_x, btn_y + btn_pad_y - btn_bbox[1]),
        btn_text, fill=WHITE + (255,), font=font_btn
    )

    return img


def overlay_logo_on_image(image_path, logo, position="bottom_right", scale=0.15):
    """
    Overlay the Heijmans logo on an image.

    position: "bottom_right", "bottom_left", "top_right", "top_left", "center_bottom"
    scale: logo width as fraction of image width
    """
    img = Image.open(image_path).convert("RGBA")

    # Scale logo to target width
    target_w = int(img.width * scale)
    if logo.width == 0:
        print("  ⚠️ Logo has zero width, skipping overlay")
        return img.convert("RGB")
    ratio = target_w / logo.width
    target_h = int(logo.height * ratio)
    logo_scaled = logo.resize((target_w, target_h), Image.LANCZOS)

    # Calculate position
    margin = int(img.width * 0.03)

    positions = {
        "bottom_right": (img.width - target_w - margin, img.height - target_h - margin),
        "bottom_left": (margin, img.height - target_h - margin),
        "top_right": (img.width - target_w - margin, margin),
        "top_left": (margin, margin),
        "center_bottom": ((img.width - target_w) // 2, img.height - target_h - margin * 2),
    }

    pos = positions.get(position, positions["bottom_right"])

    # Add semi-transparent white background behind logo for readability
    bg = Image.new("RGBA", (target_w + 16, target_h + 12), (255, 255, 255, 180))
    img.paste(bg, (pos[0] - 8, pos[1] - 6), bg)
    img.paste(logo_scaled, pos, logo_scaled)

    return img.convert("RGB")


def main():
    parser = argparse.ArgumentParser(description="Heijmans logo overlay tool")
    parser.add_argument("--logo-only", action="store_true", help="Only generate logo PNG")
    parser.add_argument("--endframe", action="store_true", help="Also generate end frame")
    parser.add_argument("--no-overlay", action="store_true", help="Skip image overlays")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    # === Step 1: Generate logo PNGs ===
    print("=== Generating Heijmans logo ===")

    # Large version (for end frame / print)
    logo_large = create_heijmans_logo(size=200)
    logo_large.save(OUTPUT_DIR / "heijmans_logo_large.png")
    print(f"  ✅ heijmans_logo_large.png ({logo_large.size[0]}×{logo_large.size[1]})")

    # Medium version (for image overlays)
    logo_medium = create_heijmans_logo(size=100)
    logo_medium.save(OUTPUT_DIR / "heijmans_logo_medium.png")
    print(f"  ✅ heijmans_logo_medium.png ({logo_medium.size[0]}×{logo_medium.size[1]})")

    # Small version (for corner watermarks)
    logo_small = create_heijmans_logo(size=60)
    logo_small.save(OUTPUT_DIR / "heijmans_logo_small.png")
    print(f"  ✅ heijmans_logo_small.png ({logo_small.size[0]}×{logo_small.size[1]})")

    # White version (for dark backgrounds)
    logo_white = create_heijmans_logo(size=100)
    # Replace navy with white in the logo
    data = logo_white.getdata()
    new_data = []
    for pixel in data:
        r, g, b, a = pixel
        # Match exact NAVY (0,58,112) with ±20 tolerance
        if abs(r - 0) <= 20 and abs(g - 58) <= 20 and abs(b - 112) <= 20 and a > 0:
            new_data.append((255, 255, 255, a))
        else:
            new_data.append(pixel)
    logo_white.putdata(new_data)
    logo_white.save(OUTPUT_DIR / "heijmans_logo_white.png")
    print(f"  ✅ heijmans_logo_white.png (white on transparent)")

    if args.logo_only:
        print("\nDone (logo-only mode).")
        return

    # === Step 2: Generate end frame ===
    if args.endframe:
        print("\n=== Generating end frame ===")
        endframe = create_endframe()
        endframe_path = OUTPUT_DIR / "endframe_1080x1920.png"
        endframe.save(endframe_path)
        print(f"  ✅ endframe_1080x1920.png ({endframe.size[0]}×{endframe.size[1]})")

    if args.no_overlay:
        print("\nDone (no-overlay mode).")
        return

    # === Step 3: Overlay logo on reference images ===
    print("\n=== Overlaying logo on reference images ===")

    # Image-specific overlay config
    overlay_config = {
        "B1-arrival.png": {"position": "bottom_left", "scale": 0.12},
        "B2-briefing.png": {"position": "bottom_right", "scale": 0.12},
        "B3-lunch.png": {"position": "bottom_right", "scale": 0.12},
        "B4-site-wide.png": {"position": "bottom_right", "scale": 0.12},
        "character.png": {"position": "bottom_left", "scale": 0.15},
        "char-front.png": {"position": "bottom_left", "scale": 0.15},
        "char-3quarter.png": {"position": "bottom_left", "scale": 0.15},
        "logo-closeup.png": {"position": "bottom_right", "scale": 0.10},
    }

    for filename, config in overlay_config.items():
        src = FINAL_DIR / filename
        if not src.exists():
            print(f"  ⏭️  {filename} not found, skipping")
            continue

        result = overlay_logo_on_image(src, logo_medium, **config)
        out_path = OUTPUT_DIR / filename
        save_kwargs = {}
        if out_path.suffix.lower() in (".jpg", ".jpeg"):
            save_kwargs["quality"] = 95
        result.save(out_path, **save_kwargs)
        print(f"  ✅ {filename} → branded/{filename}")

    print(f"\n✅ All done! Branded images in: {OUTPUT_DIR}/")
    print(f"   Logo PNGs in: {OUTPUT_DIR}/heijmans_logo_*.png")


if __name__ == "__main__":
    main()
