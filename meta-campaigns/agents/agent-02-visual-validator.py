#!/usr/bin/env python3
"""
Agent 02 — Visual Validator
Valideert 4 PNG visuals op Meta Ads specificaties (1080x1080px, bestandsgrootte, etc.)
"""

import argparse
import json
import os
import struct
import sys
import zlib
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CAMPAIGNS_DIR = BASE_DIR / "campaigns"

META_SPECS = {
    "width": 1080,
    "height": 1080,
    "format": "PNG",
    "max_size_mb": 30,
    "min_size_kb": 10,
    "aspect_ratio": "1:1",
}

AD_TYPES = [
    "schaarste",    # "Maar 3 plaatsen vrij"
    "kosten",       # Salaris/voordelen focus
    "social_proof", # "47 monteurs gingen je voor"
    "urgentie",     # Deadline / tijdsdruk
]


def read_png_dimensions(path: Path) -> tuple[int, int] | None:
    """Lees PNG dimensies uit header zonder PIL."""
    try:
        with open(path, "rb") as f:
            sig = f.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return None
            f.read(4)  # chunk length
            chunk_type = f.read(4)
            if chunk_type != b"IHDR":
                return None
            width = struct.unpack(">I", f.read(4))[0]
            height = struct.unpack(">I", f.read(4))[0]
            return width, height
    except Exception:
        return None


def validate_visual(path: Path, ad_type: str) -> dict:
    result = {
        "file": path.name,
        "ad_type": ad_type,
        "exists": path.exists(),
        "checks": {},
        "ok": False,
        "errors": [],
        "warnings": [],
    }

    if not path.exists():
        result["errors"].append(f"Bestand niet gevonden: {path}")
        return result

    # Formaat check
    result["checks"]["format"] = path.suffix.upper() == ".PNG"
    if not result["checks"]["format"]:
        result["errors"].append(f"Verwacht PNG, kreeg: {path.suffix}")

    # Bestandsgrootte
    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    size_kb = size_bytes / 1024
    result["checks"]["max_size"] = size_mb <= META_SPECS["max_size_mb"]
    result["checks"]["min_size"] = size_kb >= META_SPECS["min_size_kb"]
    result["size_mb"] = round(size_mb, 2)

    if not result["checks"]["max_size"]:
        result["errors"].append(f"Te groot: {size_mb:.1f}MB (max {META_SPECS['max_size_mb']}MB)")
    if not result["checks"]["min_size"]:
        result["warnings"].append(f"Erg klein: {size_kb:.0f}KB — mogelijk corrupt?")

    # Dimensies
    dims = read_png_dimensions(path)
    if dims:
        w, h = dims
        result["width"] = w
        result["height"] = h
        result["checks"]["width"] = w == META_SPECS["width"]
        result["checks"]["height"] = h == META_SPECS["height"]
        result["checks"]["square"] = w == h

        if not result["checks"]["width"] or not result["checks"]["height"]:
            result["errors"].append(
                f"Verkeerde afmetingen: {w}x{h}px (verwacht {META_SPECS['width']}x{META_SPECS['height']}px)"
            )
        if not result["checks"]["square"]:
            result["errors"].append("Niet vierkant (1:1 vereist voor Meta feed)")
    else:
        result["errors"].append("Kon PNG dimensies niet lezen — mogelijk corrupt")

    result["ok"] = len(result["errors"]) == 0
    return result


def find_visuals(campagne_dir: Path) -> dict[str, Path]:
    """Zoek visuals op in assets/ of campagne dir."""
    assets_dir = campagne_dir / "assets"
    visuals = {}

    for ad_type in AD_TYPES:
        # Probeer meerdere naamvarianten
        candidates = [
            campagne_dir / f"{ad_type}.png",
            campagne_dir / f"visual-{ad_type}.png",
            assets_dir / f"{ad_type}.png",
            assets_dir / f"visual-{ad_type}.png",
            BASE_DIR / "assets" / f"{ad_type}.png",
        ]
        for c in candidates:
            if c.exists():
                visuals[ad_type] = c
                break
        else:
            # Niet gevonden, gebruik verwacht pad
            visuals[ad_type] = assets_dir / f"{ad_type}.png"

    return visuals


def print_report(results: list[dict], all_ok: bool):
    print("\n=== Visual Validatie Rapport ===\n")
    for r in results:
        status = "OK" if r["ok"] else "FAIL"
        dims = f"{r.get('width', '?')}x{r.get('height', '?')}px" if "width" in r else "?"
        size = f"{r.get('size_mb', '?')}MB"
        print(f"  [{status}] {r['ad_type']:15s} — {r['file']} ({dims}, {size})")
        for err in r["errors"]:
            print(f"           FOUT: {err}")
        for warn in r["warnings"]:
            print(f"           WARN: {warn}")

    print()
    if all_ok:
        print("Alle 4 visuals valide voor Meta Ads upload.")
    else:
        failed = [r["ad_type"] for r in results if not r["ok"]]
        print(f"Validatie mislukt voor: {', '.join(failed)}")
        print("\nVerwachte specs:")
        print(f"  - Formaat: PNG")
        print(f"  - Afmetingen: {META_SPECS['width']}x{META_SPECS['height']}px")
        print(f"  - Max grootte: {META_SPECS['max_size_mb']}MB")
        print(f"  - Aspect ratio: {META_SPECS['aspect_ratio']}")
        print(f"\nGenereer visuals met Agent skills/skill-nano-banana.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campagne", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--assets-dir", help="Pad naar visuals map")
    args = parser.parse_args()

    campagne = args.campagne
    campagne_dir = CAMPAIGNS_DIR / campagne.replace(" ", "_")
    campagne_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Agent 02: Visual Validator ===")
    print(f"Campagne: {campagne}")

    if args.assets_dir:
        assets_base = Path(args.assets_dir)
        visuals = {ad_type: assets_base / f"{ad_type}.png" for ad_type in AD_TYPES}
    else:
        visuals = find_visuals(campagne_dir)

    print(f"\nZoeken naar visuals...")
    for ad_type, path in visuals.items():
        status = "gevonden" if path.exists() else "NIET GEVONDEN"
        print(f"  {ad_type:15s}: {path} [{status}]")

    missing = [ad_type for ad_type, path in visuals.items() if not path.exists()]
    if missing and not args.dry_run:
        print(f"\nOntbrekende visuals: {', '.join(missing)}")
        doorgaan = input("Toch doorgaan met validatie? [j/n]: ").strip().lower()
        if doorgaan != "j":
            print("Geannuleerd. Genereer eerst alle 4 visuals.")
            sys.exit(1)

    results = []
    for ad_type, path in visuals.items():
        r = validate_visual(path, ad_type)
        results.append(r)

    all_ok = all(r["ok"] for r in results)
    print_report(results, all_ok)

    # Sla rapport op
    report_path = campagne_dir / "visual-validation-report.json"
    report_data = {
        "campagne": campagne,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "all_ok": all_ok,
        "results": results,
    }
    report_path.write_text(json.dumps(report_data, indent=2))
    print(f"\nRapport opgeslagen: {report_path}")

    if not all_ok and not args.dry_run:
        sys.exit(1)

    print("\nAgent 02 klaar.")


if __name__ == "__main__":
    main()
