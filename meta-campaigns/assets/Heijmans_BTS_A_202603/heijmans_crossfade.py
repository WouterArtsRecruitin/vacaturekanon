#!/usr/bin/env python3
"""
Heijmans BTS — Senior Uitvoerder Wegen — Crossfade Assembly

Assembleert 3 clips met vloeiende xfade overgangen.
Input clips worden geschaald/gecropped naar 1080x1920 (9:16).

Presets:
  briefing-tot-asfalt  (A) golden-hour → dusk → night closeup
  nachtploeg           (B) dusk → night closeup → night wide
  uitvoerder           (C) golden-hour discussion → dusk → night wide

Usage:
  python3 heijmans_crossfade.py                          # Default: preset A
  python3 heijmans_crossfade.py --preset nachtploeg      # Preset B
  python3 heijmans_crossfade.py --preset uitvoerder      # Preset C
  python3 heijmans_crossfade.py --all                    # Render alle 3
  python3 heijmans_crossfade.py --clips a.mp4 b.mp4 c.mp4  # Custom
  python3 heijmans_crossfade.py --fade 1.0               # Langere crossfade
  python3 heijmans_crossfade.py --preview                # Dry-run: toon volgorde + timing
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "videos"
OUTPUT_DIR = BASE_DIR / "output"

PRESETS = {
    "briefing-tot-asfalt": {
        "clips": [
            "golden-hour-briefing.mp4",
            "dusk-briefing.mp4",
            "night-crew-closeup.mp4",
        ],
        "description": "Van Briefing tot Asfalt — dag→schemering→nacht",
        "suffix": "A_briefing_tot_asfalt",
    },
    "nachtploeg": {
        "clips": [
            "dusk-briefing.mp4",
            "night-crew-closeup.mp4",
            "night-paver-wide.mp4",
        ],
        "description": "Nachtploeg — schemering→crew closeup→wide machines",
        "suffix": "B_nachtploeg",
    },
    "uitvoerder": {
        "clips": [
            "golden-hour-discussion.mp4",
            "dusk-briefing.mp4",
            "night-paver-wide.mp4",
        ],
        "description": "De Uitvoerder — discussie→toezicht→resultaat",
        "suffix": "C_uitvoerder",
    },
}

TARGET_W = 1080
TARGET_H = 1920
FPS = 24
CRF = 18


def get_duration(clip_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=duration",
            "-of", "csv=p=0",
            str(clip_path),
        ],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def build_filter(durations: list[float], fade: float) -> str:
    """Build ffmpeg filter_complex for 3 clips with xfade transitions."""
    # Scale each input: crop to 9:16 center, then scale to target
    # For square 1440x1440 input → crop center 1440x(1440*16/9) won't work (too tall)
    # Instead: crop width to h*9/16, then scale
    # 1440x1440 → need 810x1440 crop → scale to 1080x1920
    # Actually for square: crop to 9:16 aspect = take full height, crop width to h*9/16
    # 1440 * 9/16 = 810 → crop 810x1440 center → scale 1080x1920
    filters = []
    for i in range(3):
        # Generic: crop to 9:16 aspect ratio (center), then scale + fps + pixel format
        filters.append(
            f"[{i}:v]"
            f"crop=ih*9/16:ih,"
            f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=disable,"
            f"fps={FPS},format=yuv420p,setsar=1"
            f"[v{i}]"
        )

    # First xfade: v0 + v1
    offset1 = durations[0] - fade
    filters.append(
        f"[v0][v1]xfade=transition=fade:duration={fade}:offset={offset1:.3f}[vt1]"
    )

    # Second xfade: vt1 + v2
    offset2 = offset1 + durations[1] - fade
    filters.append(
        f"[vt1][v2]xfade=transition=fade:duration={fade}:offset={offset2:.3f}[vout]"
    )

    return ";".join(filters)


def render(clips: list[Path], output_path: Path, fade: float, dry_run: bool = False):
    durations = [get_duration(c) for c in clips]
    total = sum(durations) - 2 * fade

    print(f"\n  Clips:")
    for i, (c, d) in enumerate(zip(clips, durations)):
        print(f"    [{i+1}] {c.name} ({d:.1f}s)")
    print(f"  Crossfade: {fade}s")
    print(f"  Totaal: ~{total:.1f}s")
    print(f"  Output: {output_path.name}")

    if dry_run:
        print("  [PREVIEW — niet gerenderd]")
        return True

    filter_complex = build_filter(durations, fade)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(clips[0]),
        "-i", str(clips[1]),
        "-i", str(clips[2]),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-crf", str(CRF),
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        str(output_path),
    ]

    print(f"\n  Rendering...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  FOUT: ffmpeg failed\n{result.stderr[-500:]}")
        return False

    # Verify output
    out_dur = get_duration(output_path)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  OK: {out_dur:.1f}s, {size_mb:.1f} MB")
    return True


def main():
    parser = argparse.ArgumentParser(description="Heijmans BTS crossfade assembly")
    parser.add_argument("--preset", default="briefing-tot-asfalt",
                        choices=list(PRESETS.keys()),
                        help="Video preset (default: briefing-tot-asfalt)")
    parser.add_argument("--clips", nargs=3, metavar="CLIP",
                        help="3 custom clips (overrides preset)")
    parser.add_argument("--fade", type=float, default=0.8,
                        help="Crossfade duur in seconden (default: 0.8)")
    parser.add_argument("--all", action="store_true",
                        help="Render alle 3 presets")
    parser.add_argument("--preview", action="store_true",
                        help="Dry-run: toon volgorde + timing zonder te renderen")
    parser.add_argument("--output", type=str, help="Custom output path")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.all:
        print("=== Heijmans BTS — Alle presets ===")
        ok = True
        for name, preset in PRESETS.items():
            print(f"\n--- {preset['description']} ---")
            clips = [VIDEOS_DIR / c for c in preset["clips"]]
            missing = [c for c in clips if not c.exists()]
            if missing:
                print(f"  SKIP: ontbreekt {[m.name for m in missing]}")
                ok = False
                continue
            out = OUTPUT_DIR / f"Heijmans_BTS_{preset['suffix']}.mp4"
            if not render(clips, out, args.fade, args.preview):
                ok = False
        return 0 if ok else 1

    if args.clips:
        clips = [Path(c) if Path(c).is_absolute() else VIDEOS_DIR / c for c in args.clips]
        out_name = args.output or "Heijmans_BTS_custom.mp4"
    else:
        preset = PRESETS[args.preset]
        clips = [VIDEOS_DIR / c for c in preset["clips"]]
        out_name = args.output or f"Heijmans_BTS_{preset['suffix']}.mp4"
        print(f"=== {preset['description']} ===")

    missing = [c for c in clips if not c.exists()]
    if missing:
        print(f"FOUT: clips niet gevonden: {[m.name for m in missing]}")
        return 1

    out_path = Path(out_name) if Path(out_name).is_absolute() else OUTPUT_DIR / out_name
    success = render(clips, out_path, args.fade, args.preview)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
