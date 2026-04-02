#!/usr/bin/env python3
"""
assemble_bts_v2.py — Heijmans BTS "Achter de Schermen" v2 assembly.

Montage (strak, 4 scenes + end card):
  [Clapperboard 3.5s] → hard cut →
  [Interview 5s] → smash cut →
  [Meanwhile... 0.8s] → hard cut →
  [Tekst vergeten 4s] → hard cut →
  [Dura Vermeer truck 4.5s] → fade to black →
  [End card 3s: Senior Uitvoerder Wegen — Heijmans]

Target: ~20s, 1080x1920, 24fps
"""
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
V2_DIR = BASE_DIR / "videos" / "bts_bloopers_v2"
OUTPUT_DIR = BASE_DIR / "output"

W, H, FPS, CRF = 1080, 1920, 24, 18

CLIPS = [
    ("1_clapperboard.mp4", 0, 3.5),
    ("2_interview.mp4", 0, 5.0),
]
BLOOPER_CLIPS = [
    ("4a_forgot_lines.mp4", 0, 4.0),
    ("4b_wrong_truck_branded.mp4", 0, 4.5),
]
MEANWHILE_DUR = 0.8
ENDCARD_DUR = 3.0


def run(cmd, desc=""):
    if desc:
        print(f"  {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[-500:]}")
        sys.exit(1)


def trim_scale(src, dst, start, end):
    run([
        "ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", str(src),
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p,setsar=1",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-an", str(dst),
    ], f"Trim {src.name} [{start}-{end}s]")


def make_frame(img, output_path, duration):
    """PIL Image → video clip."""
    img_path = Path(tempfile.mktemp(suffix=".png"))
    img.save(str(img_path))
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(img_path),
        "-t", str(duration),
        "-vf", f"fps={FPS},format=yuv420p",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-an",
        str(output_path),
    ], f"Frame clip ({duration}s)")
    img_path.unlink(missing_ok=True)


def get_font(size):
    for fp in ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial Bold.ttf"]:
        try:
            return ImageFont.truetype(fp, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def create_meanwhile():
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(56)
    text = "Meanwhile..."
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - tw) / 2, (H - th) / 2), text, fill=(255, 255, 255), font=font)
    return img


def create_endcard():
    """End card: Heijmans branding + vacancy."""
    # Dark background with Heijmans orange accent
    img = Image.new("RGB", (W, H), (20, 20, 25))
    draw = ImageDraw.Draw(img)

    # Orange accent bar at top
    draw.rectangle([(0, 0), (W, 8)], fill=(230, 99, 10))

    # Heijmans text (large)
    font_big = get_font(72)
    font_sub = get_font(38)
    font_small = get_font(28)

    # "Heijmans" centered
    text = "Heijmans"
    bbox = draw.textbbox((0, 0), text, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 - 140), text, fill=(230, 99, 10), font=font_big)

    # Vacancy title
    text = "Senior Uitvoerder Wegen"
    bbox = draw.textbbox((0, 0), text, font=font_sub)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 - 30), text, fill=(255, 255, 255), font=font_sub)

    # Tagline
    text = "Echt werk. Echte mensen."
    bbox = draw.textbbox((0, 0), text, font=font_small)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 + 40), text, fill=(160, 160, 170), font=font_small)

    # Orange accent bar at bottom
    draw.rectangle([(0, H - 8), (W, H)], fill=(230, 99, 10))

    return img


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(prefix="bts_v2_"))
    print(f"=== Heijmans BTS Bloopers v2 — Assembly ===\n")

    # 1. Trim + scale main clips
    print("--- Trim & Scale ---")
    trimmed_main = []
    for filename, start, end in CLIPS:
        src = V2_DIR / filename
        dst = tmpdir / f"main_{filename}"
        trim_scale(src, dst, start, end)
        trimmed_main.append(dst)

    # 2. Meanwhile frame
    print("\n--- Meanwhile ---")
    meanwhile_path = tmpdir / "meanwhile.mp4"
    make_frame(create_meanwhile(), meanwhile_path, MEANWHILE_DUR)

    # 3. Trim + scale blooper clips
    print("\n--- Bloopers ---")
    trimmed_bloopers = []
    for filename, start, end in BLOOPER_CLIPS:
        src = V2_DIR / filename
        dst = tmpdir / f"blooper_{filename}"
        trim_scale(src, dst, start, end)
        trimmed_bloopers.append(dst)

    # 4. Fade-to-black on last blooper
    last_blooper = trimmed_bloopers[-1]
    last_faded = tmpdir / "last_faded.mp4"
    last_dur = BLOOPER_CLIPS[-1][2] - BLOOPER_CLIPS[-1][1]
    run([
        "ffmpeg", "-y", "-i", str(last_blooper),
        "-vf", f"fade=t=out:st={last_dur - 0.6}:d=0.6",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an", str(last_faded),
    ], "Fade-to-black last blooper")
    trimmed_bloopers[-1] = last_faded

    # 5. End card
    print("\n--- End Card ---")
    endcard_path = tmpdir / "endcard.mp4"
    endcard_img = create_endcard()
    # Fade-in on end card
    endcard_raw = tmpdir / "endcard_raw.mp4"
    make_frame(endcard_img, endcard_raw, ENDCARD_DUR)
    run([
        "ffmpeg", "-y", "-i", str(endcard_raw),
        "-vf", f"fade=t=in:st=0:d=0.4",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an", str(endcard_path),
    ], "End card fade-in")

    # 6. Concat all parts
    print("\n--- Final Concat ---")
    parts = trimmed_main + [meanwhile_path] + trimmed_bloopers + [endcard_path]

    concat_list = tmpdir / "concat.txt"
    with open(concat_list, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")

    output = OUTPUT_DIR / "Heijmans_BTS_Bloopers_v2.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "libx264", "-crf", str(CRF), "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(output),
    ], "Final concat")

    # Verify
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,duration,r_frame_rate",
         "-of", "csv=p=0", str(output)],
        capture_output=True, text=True,
    )
    mb = output.stat().st_size / (1024 * 1024)
    print(f"\n=== DONE ===")
    print(f"Output: {output.name}")
    print(f"Specs: {result.stdout.strip()}")
    print(f"Size: {mb:.1f} MB")

    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
