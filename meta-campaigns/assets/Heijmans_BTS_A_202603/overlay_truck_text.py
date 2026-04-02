#!/usr/bin/env python3
"""Overlay 'DURA VERMEER' text on the green truck in 4b_wrong_truck.mp4."""
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
INPUT = BASE_DIR / "videos" / "bts_bloopers_v2" / "4b_wrong_truck.mp4"
OUTPUT = BASE_DIR / "videos" / "bts_bloopers_v2" / "4b_wrong_truck_branded.mp4"

# Text config — positioned on the green truck (left side of frame)
TEXT = "DURA VERMEER"
FONT_SIZE = 26
TEXT_COLOR = (0, 40, 120, 240)  # donkerblauw — Dura Vermeer merkkleur
SHADOW_COLOR = (0, 0, 0, 0)    # geen schaduw — echt logo heeft geen schaduw
# Position on truck door panel (green cab door, left side)
TEXT_X = 12
TEXT_Y = 635


def create_text_overlay(width, height):
    """Create transparent PNG with DURA VERMEER text."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try system fonts
    font = None
    for font_name in [
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFCompact.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_name, FONT_SIZE)
            break
        except (IOError, OSError):
            continue
    if not font:
        font = ImageFont.load_default()

    # Shadow
    draw.text((TEXT_X + 2, TEXT_Y + 2), TEXT, fill=SHADOW_COLOR, font=font)
    # Main text
    draw.text((TEXT_X, TEXT_Y), TEXT, fill=TEXT_COLOR, font=font)

    return img


def main():
    # Get video dimensions
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(INPUT)],
        capture_output=True, text=True
    )
    w, h = map(int, result.stdout.strip().split(","))
    print(f"Video: {w}x{h}")

    # Create overlay image
    overlay = create_text_overlay(w, h)
    overlay_path = Path(tempfile.mktemp(suffix=".png"))
    overlay.save(str(overlay_path))
    print(f"Overlay saved: {overlay_path}")

    # Composite with ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", str(INPUT),
        "-i", str(overlay_path),
        "-filter_complex", "[0:v][1:v]overlay=0:0",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
        str(OUTPUT),
    ]

    print("Rendering overlay...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[-300:]}")
        return

    mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"Done: {OUTPUT.name} ({mb:.1f} MB)")

    # Cleanup
    overlay_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
