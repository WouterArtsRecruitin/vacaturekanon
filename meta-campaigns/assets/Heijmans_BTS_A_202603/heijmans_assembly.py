#!/usr/bin/env python3
"""
heijmans_assembly.py — Assemble Heijmans BTS video from Kling clips

Combines B1 + B2 + B3 clips into a 15-17s 9:16 video with:
- Text overlay: "Niet aankomen, verse laag" (briefje grap)
- End frame: Heijmans branding + vacancy CTA
- Optional background music

Usage:
    python3 heijmans_assembly.py                    # Full assembly
    python3 heijmans_assembly.py --preview          # Generate concat list only
    python3 heijmans_assembly.py --no-endframe      # Skip end frame
    python3 heijmans_assembly.py --music bg.mp3     # Add background music
"""

import argparse
import json
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "videos"
BRANDED_DIR = BASE_DIR / "branded"
OUTPUT_DIR = BASE_DIR / "output"

# Video specs
WIDTH = 1080
HEIGHT = 1920
FPS = 24

# Clip selection (order matters)
CLIPS = [
    {
        "file": "B1-lunch-v5.mp4",
        "fallback": "B1-lunch-v4.mp4",
        "label": "B1 — Lunch schouderklop",
        "overlay": {
            "text": "Niet aankomen,\nverse laag",
            "font_size": 28,
            "style": "handwritten",
            "position": "bottom_right",
            "start": 3.5,
            "end": 5.0,
            "rotation": -8,
        },
    },
    {
        "file": "B3-lunch.mp4",
        "label": "B3 — Lunch sfeer (buffer)",
        "overlay": None,
    },
    {
        "file": "B2-briefing-v3.mp4",
        "fallback": "B2-briefing-v2.mp4",
        "label": "B2 — Briefing reveal",
        "overlay": None,
    },
]

# End frame duration
ENDFRAME_DURATION = 2.5  # seconds


def check_ffmpeg():
    """Verify ffmpeg is available."""
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found. Install with: brew install ffmpeg")
        return False
    return True


def find_clip(clip_config):
    """Find the best available clip file."""
    primary = VIDEOS_DIR / clip_config["file"]
    if primary.exists():
        return primary

    fallback = clip_config.get("fallback")
    if fallback:
        fb_path = VIDEOS_DIR / fallback
        if fb_path.exists():
            print(f"  Using fallback: {fallback}")
            return fb_path

    return None


def get_video_duration(path):
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"  ⚠️ Could not get duration for {path}: {e}")
        return 5.0  # fallback duration


def scale_clip_to_9x16(input_path, output_path):
    """
    Scale/crop a clip to exactly 1080x1920 (9:16).
    Handles various input aspect ratios.
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"fps={FPS}"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",  # strip audio (we'll add music later)
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ scale error: {result.stderr[-300:]}")
        raise RuntimeError(f"ffmpeg scale failed for {input_path}")


def add_text_overlay(input_path, output_path, overlay_config):
    """
    Add text overlay to a clip using ffmpeg drawtext.
    Simulates a "briefje" (note) stuck on someone's back.
    """
    cfg = overlay_config
    text = cfg["text"]
    fs = cfg["font_size"]
    start = cfg["start"]
    end = cfg["end"]

    # Create briefje overlay as transparent PNG using Pillow
    # Then use ffmpeg overlay filter (doesn't need libfreetype)
    briefje_path = output_path.parent / "temp_briefje.png"
    rotation = cfg.get("rotation", -8)
    _create_briefje_image(briefje_path, text, fs, rotation=rotation)

    # Scale video + overlay the briefje PNG with timed enable
    # overlay filter IS available in default ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-i", str(briefje_path),
        "-filter_complex",
        (
            f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},fps={FPS}[base];"
            f"[base][1:v]overlay=W-w-60:H-h-200"
            f":enable='between(t,{start},{end})'[out]"
        ),
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        str(output_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ⚠️ overlay error: {result.stderr[-300:]}")
            print(f"    Falling back to plain scale...")
            scale_clip_to_9x16(input_path, output_path)
    finally:
        briefje_path.unlink(missing_ok=True)


def _create_briefje_image(output_path, text, font_size=36, rotation=-8):
    """
    Create a 'briefje' (paper note) image with transparent background.
    Looks like a white sticky note with handwritten-style text.
    """
    try:
        font = ImageFont.truetype(
            "/System/Library/Fonts/HelveticaNeue.ttc", font_size, index=1
        )
    except OSError:
        font = ImageFont.load_default()

    lines = text.split("\n")

    # Measure text
    max_w = 0
    total_h = 0
    line_heights = []
    for line in lines:
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        line_heights.append(h)
        total_h += h + 8

    # Note dimensions with padding
    pad = 24
    note_w = max_w + pad * 2
    note_h = total_h + pad * 2

    # Create image
    img = Image.new("RGBA", (note_w, note_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # White paper background with slight transparency
    draw.rounded_rectangle(
        [0, 0, note_w - 1, note_h - 1],
        radius=6, fill=(255, 255, 255, 220)
    )
    # Thin border
    draw.rounded_rectangle(
        [0, 0, note_w - 1, note_h - 1],
        radius=6, outline=(100, 100, 100, 150), width=2
    )

    # Draw text lines
    y = pad
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        x = (note_w - (bbox[2] - bbox[0])) // 2
        draw.text((x, y - bbox[1]), line, fill=(30, 30, 30, 255), font=font)
        y += line_heights[i] + 8

    # Rotate slightly for realism
    img = img.rotate(rotation, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))

    img.save(output_path)


def create_endframe_video(endframe_image, output_path, duration=2.5):
    """Create a video clip from the end frame image."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(endframe_image),
        "-t", str(duration),
        "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ endframe error: {result.stderr[-300:]}")
        raise RuntimeError("ffmpeg endframe creation failed")


def concat_clips(clip_paths, output_path):
    """Concatenate clips using ffmpeg concat demuxer."""
    # Write concat file
    concat_file = output_path.parent / "concat_list.txt"
    with open(concat_file, "w") as f:
        for path in clip_paths:
            f.write(f"file '{path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ concat error: {result.stderr[-300:]}")
        raise RuntimeError("ffmpeg concat failed")
    print(f"  Concat list: {concat_file}")


def add_music(video_path, music_path, output_path):
    """Add background music to the final video, fading out at the end."""
    duration = get_video_duration(video_path)
    fade_start = max(0, duration - 2)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(music_path),
        "-filter_complex", (
            f"[1:a]afade=t=in:st=0:d=1,"
            f"afade=t=out:st={fade_start}:d=2,"
            f"volume=0.3[music]"
        ),
        "-map", "0:v", "-map", "[music]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ music error: {result.stderr[-300:]}")
        raise RuntimeError("ffmpeg music overlay failed")


def main():
    parser = argparse.ArgumentParser(description="Heijmans BTS video assembly")
    parser.add_argument("--preview", action="store_true", help="Show plan only")
    parser.add_argument("--no-endframe", action="store_true", help="Skip end frame")
    parser.add_argument("--no-briefje", action="store_true", help="Skip briefje text overlay")
    parser.add_argument("--music", type=str, help="Path to background music file")
    parser.add_argument("--output", type=str, default=None, help="Output filename")
    args = parser.parse_args()

    if not check_ffmpeg():
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    print("=== Heijmans BTS Video Assembly ===\n")

    # Step 1: Find all clips
    print("📋 Checking clips...")
    available_clips = []
    for clip in CLIPS:
        path = find_clip(clip)
        if path:
            dur = get_video_duration(path)
            print(f"  ✅ {clip['label']}: {path.name} ({dur:.1f}s)")
            available_clips.append((clip, path, dur))
        else:
            print(f"  ❌ {clip['label']}: NOT FOUND ({clip['file']})")

    if not available_clips:
        print("\n❌ No clips found. Run Kling batch first.")
        return

    # Calculate total duration
    total_dur = sum(d for _, _, d in available_clips)
    if not args.no_endframe:
        total_dur += ENDFRAME_DURATION
    print(f"\n  Total duration: {total_dur:.1f}s (target: 15-17s)")

    if args.preview:
        print("\n(Preview mode — no files generated)")
        return

    # Step 2: Process each clip
    print("\n🔧 Processing clips...")
    processed_paths = []

    for clip_config, clip_path, _ in available_clips:
        temp_name = f"temp_{clip_config['file'].replace('.mp4', '')}_processed.mp4"
        temp_path = OUTPUT_DIR / temp_name

        if clip_config.get("overlay") and not args.no_briefje:
            print(f"  Adding briefje overlay to {clip_path.name}...")
            add_text_overlay(clip_path, temp_path, clip_config["overlay"])
        else:
            print(f"  Scaling {clip_path.name} to 9:16...")
            scale_clip_to_9x16(clip_path, temp_path)

        processed_paths.append(temp_path)

    # Step 3: End frame
    if not args.no_endframe:
        endframe_img = BRANDED_DIR / "endframe_1080x1920.png"
        if endframe_img.exists():
            print(f"  Creating end frame video ({ENDFRAME_DURATION}s)...")
            endframe_vid = OUTPUT_DIR / "temp_endframe.mp4"
            create_endframe_video(endframe_img, endframe_vid, ENDFRAME_DURATION)
            processed_paths.append(endframe_vid)
        else:
            print(f"  ⚠️ End frame not found: {endframe_img}")
            print(f"     Run: python3 heijmans_logo_overlay.py --endframe")

    # Step 4: Concatenate
    print("\n🎬 Assembling final video...")
    output_name = args.output or "Heijmans_BTS_Senior_Uitvoerder_Wegen_v1.mp4"
    final_no_music = OUTPUT_DIR / f"_temp_{output_name}"
    final_path = OUTPUT_DIR / output_name

    concat_clips(processed_paths, final_no_music)

    # Step 5: Add music (optional)
    if args.music:
        music_path = Path(args.music)
        if music_path.exists():
            print(f"  Adding music: {music_path.name}...")
            add_music(final_no_music, music_path, final_path)
            final_no_music.unlink()  # clean up
        else:
            print(f"  ⚠️ Music file not found: {music_path}")
            final_no_music.rename(final_path)
    else:
        final_no_music.rename(final_path)

    # Step 6: Final stats
    final_dur = get_video_duration(final_path)
    final_size = final_path.stat().st_size / 1_000_000
    print(f"\n✅ DONE!")
    print(f"   📁 {final_path}")
    print(f"   ⏱️  {final_dur:.1f}s")
    print(f"   📦 {final_size:.1f} MB")
    print(f"   📐 {WIDTH}×{HEIGHT} (9:16)")

    # Cleanup temp files
    for p in OUTPUT_DIR.glob("temp_*"):
        p.unlink()
    print(f"\n   🧹 Temp files cleaned up")


if __name__ == "__main__":
    main()
