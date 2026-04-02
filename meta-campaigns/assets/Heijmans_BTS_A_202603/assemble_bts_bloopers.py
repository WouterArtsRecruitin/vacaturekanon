#!/usr/bin/env python3
"""
assemble_bts_bloopers.py — Heijmans BTS "Achter de Schermen" final assembly.

Montage:
  [1_clapperboard 0-3s] -hard cut-> [2_interview 0-5s] -crossfade 0.8s-> [3_hero 0-6s]
  -smash cut-> [black "Meanwhile..." 0.8s]
  -hard cut-> [4a_forgot_lines 0-3.5s] -hard cut-> [4b_wrong_truck 0-4s] -hard cut-> [4c_director 0-3.5s]
  -fade to black 0.5s->

Target: ~20s total, 1080x1920, 24fps
"""
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).parent
V2_DIR = BASE_DIR / "videos" / "bts_bloopers_v2"
OUTPUT_DIR = BASE_DIR / "output"

# Clip definitions: (file, start_sec, end_sec)
CLIPS = {
    "clapperboard": ("1_clapperboard.mp4", 0, 3.5),
    "interview": ("2_interview.mp4", 0, 5.5),
    "hero": ("3_hero.mp4", 0, 6.0),
    "forgot_lines": ("4a_forgot_lines.mp4", 0, 4.0),
    "wrong_truck": ("4b_wrong_truck_branded.mp4", 0, 4.5),
    "director": ("4c_director.mp4", 0, 4.0),
}

W, H, FPS, CRF = 1080, 1920, 24, 18
CROSSFADE = 0.8
SMASH_DUR = 0.8  # "Meanwhile..." black frame


def run(cmd, desc=""):
    print(f"  {desc}..." if desc else "  Running...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[-400:]}")
        sys.exit(1)
    return result


def trim_and_scale(input_path, output_path, start, end):
    """Trim clip and scale to 1080x1920 24fps."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-to", str(end),
        "-i", str(input_path),
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},format=yuv420p,setsar=1",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-an", str(output_path),
    ]
    run(cmd, f"Trim {input_path.name} [{start}-{end}s]")


def create_black_frame(output_path, duration, text="Meanwhile..."):
    """Create black frame with centered text using Pillow → image → ffmpeg loop."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = None
    for fp in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        try:
            font = ImageFont.truetype(fp, 64)
            break
        except (IOError, OSError):
            continue
    if not font:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((W - tw) / 2, (H - th) / 2), text, fill=(255, 255, 255), font=font)

    img_path = Path(tempfile.mktemp(suffix=".png"))
    img.save(str(img_path))

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img_path),
        "-t", str(duration),
        "-vf", f"fps={FPS},format=yuv420p",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-an", str(output_path),
    ]
    run(cmd, f"Black frame '{text}' ({duration}s)")
    img_path.unlink(missing_ok=True)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(prefix="heijmans_bts_"))
    print(f"=== Heijmans BTS Bloopers — Assembly ===\n")
    print(f"Temp: {tmpdir}\n")

    # Step 1: Trim and scale all clips
    print("--- Step 1: Trim & Scale ---")
    trimmed = {}
    for name, (filename, start, end) in CLIPS.items():
        src = V2_DIR / filename
        if not src.exists():
            print(f"  MISSING: {filename}")
            sys.exit(1)
        dst = tmpdir / f"{name}.mp4"
        trim_and_scale(src, dst, start, end)
        trimmed[name] = dst

    # Step 2: Create "Meanwhile..." black frame
    print("\n--- Step 2: Meanwhile frame ---")
    meanwhile = tmpdir / "meanwhile.mp4"
    create_black_frame(meanwhile, SMASH_DUR)

    # Step 3: Crossfade interview → hero
    print("\n--- Step 3: Crossfade interview→hero ---")
    interview_dur = CLIPS["interview"][2] - CLIPS["interview"][1]
    xfade_offset = interview_dur - CROSSFADE

    crossfaded = tmpdir / "interview_hero.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(trimmed["interview"]),
        "-i", str(trimmed["hero"]),
        "-filter_complex",
        f"[0:v][1:v]xfade=transition=fade:duration={CROSSFADE}:offset={xfade_offset:.3f}[vout]",
        "-map", "[vout]",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an",
        str(crossfaded),
    ]
    run(cmd, "Crossfade interview→hero")

    # Step 4: Concat everything with hard cuts
    # Order: clapperboard | interview_hero (crossfaded) | meanwhile | forgot | truck | director
    print("\n--- Step 4: Final concat ---")

    # Add fade-to-black on last clip
    director_faded = tmpdir / "director_faded.mp4"
    director_dur = CLIPS["director"][2] - CLIPS["director"][1]
    fade_start = director_dur - 0.5
    cmd = [
        "ffmpeg", "-y",
        "-i", str(trimmed["director"]),
        "-vf", f"fade=t=out:st={fade_start}:d=0.5",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an",
        str(director_faded),
    ]
    run(cmd, "Fade-to-black on director")

    # Build concat list
    concat_list = tmpdir / "concat.txt"
    parts = [
        trimmed["clapperboard"],
        crossfaded,
        meanwhile,
        trimmed["forgot_lines"],
        trimmed["wrong_truck"],
        director_faded,
    ]
    with open(concat_list, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")

    output = OUTPUT_DIR / "Heijmans_BTS_Bloopers_v1.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-crf", str(CRF), "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-an", str(output),
    ]
    run(cmd, "Final concat")

    # Verify
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,duration,r_frame_rate",
         "-of", "csv=p=0", str(output)],
        capture_output=True, text=True,
    )
    specs = result.stdout.strip()
    mb = output.stat().st_size / (1024 * 1024)
    print(f"\n=== DONE ===")
    print(f"Output: {output}")
    print(f"Specs: {specs}")
    print(f"Size: {mb:.1f} MB")

    # Cleanup temp
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
