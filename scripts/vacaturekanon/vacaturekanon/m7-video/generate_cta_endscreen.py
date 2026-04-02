#!/usr/bin/env python3
"""
generate_cta_endscreen.py — Vacaturekanon CTA End Screen Generator
Genereert een branded 5-seconden CTA end frame (1080×1920, 9:16) via Pillow + FFmpeg.
Output: cta_endscreen.mp4
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def darken(rgb: tuple, factor: float = 0.25) -> tuple:
    return tuple(int(c * factor) for c in rgb)


def lighten(rgb: tuple, amount: int = 60) -> tuple:
    return tuple(min(255, c + amount) for c in rgb)


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Probeer systeemfonts te laden — fallback naar default."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_cta_image(
    klant: str,
    rol: str,
    contact_naam: str,
    contact_tel: str,
    contact_email: str,
    website: str,
    primaire_kleur: str = "#0066CC",
) -> Image.Image:
    """Render CTA frame als PIL Image (1080×1920)."""

    W, H = 1080, 1920
    brand_rgb  = hex_to_rgb(primaire_kleur)
    bg_rgb     = darken(brand_rgb, 0.12)
    strip_rgb  = brand_rgb
    white      = (255, 255, 255)
    light_gray = (200, 210, 220)
    brand_light= lighten(brand_rgb, 40)

    img  = Image.new("RGB", (W, H), color=bg_rgb)
    draw = ImageDraw.Draw(img)

    # ── Fonts ──────────────────────────────────────────────────────────────
    f_xs    = get_font(32)
    f_sm    = get_font(40)
    f_md    = get_font(52)
    f_lg    = get_font(68)
    f_xl    = get_font(90)

    # ── Gekleurde balk bovenaan (accent) ───────────────────────────────────
    draw.rectangle([0, 0, W, 16], fill=strip_rgb)

    # ── Logo placeholder tekst ─────────────────────────────────────────────
    logo_text = klant.upper()
    bbox = draw.textbbox((0, 0), logo_text, font=f_md)
    lw  = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, 80), logo_text, font=f_md, fill=brand_light)

    # ── Dunne lijn onder logo ──────────────────────────────────────────────
    draw.rectangle([80, 180, W - 80, 184], fill=(*brand_rgb, 100))

    # ── "OPEN VACATURE" label ──────────────────────────────────────────────
    label = "OPEN VACATURE"
    bbox  = draw.textbbox((0, 0), label, font=f_xs)
    lw    = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, 260), label, font=f_xs, fill=brand_light)

    # ── Rol titel (groot) ──────────────────────────────────────────────────
    # Split op "/" voor tweeregelopmaak indien lang
    if len(rol) > 20 and "/" in rol:
        parts = [p.strip() for p in rol.split("/", 1)]
    elif len(rol) > 22 and "|" in rol:
        parts = [p.strip() for p in rol.split("|", 1)]
    else:
        parts = [rol]

    rol_y = 340
    for part in parts:
        bbox = draw.textbbox((0, 0), part, font=f_xl)
        lw   = bbox[2] - bbox[0]
        draw.text(((W - lw) // 2, rol_y), part, font=f_xl, fill=white)
        rol_y += 108

    # ── "bij Klant" ────────────────────────────────────────────────────────
    bij_text = f"bij {klant}"
    bbox = draw.textbbox((0, 0), bij_text, font=f_sm)
    lw   = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, rol_y + 20), bij_text, font=f_sm, fill=light_gray)

    # ── Divider ────────────────────────────────────────────────────────────
    div_y = rol_y + 130
    draw.rectangle([80, div_y, W - 80, div_y + 2], fill=strip_rgb)

    # ── "Interesse? Neem contact op" ───────────────────────────────────────
    interest = "Interesse? Neem contact op:"
    bbox = draw.textbbox((0, 0), interest, font=f_xs)
    lw   = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, div_y + 30), interest, font=f_xs, fill=light_gray)

    # ── Contact naam ───────────────────────────────────────────────────────
    cn_y = div_y + 110
    bbox = draw.textbbox((0, 0), contact_naam, font=f_lg)
    lw   = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, cn_y), contact_naam, font=f_lg, fill=white)

    # ── Telefoon ───────────────────────────────────────────────────────────
    tel_y = cn_y + 100
    bbox  = draw.textbbox((0, 0), contact_tel, font=f_md)
    lw    = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, tel_y), contact_tel, font=f_md, fill=brand_light)

    # ── Email ──────────────────────────────────────────────────────────────
    email_y = tel_y + 80
    bbox    = draw.textbbox((0, 0), contact_email, font=f_sm)
    lw      = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, email_y), contact_email, font=f_sm, fill=light_gray)

    # ── Gekleurde balk onderaan ────────────────────────────────────────────
    strip_h   = 130
    strip_top = H - strip_h
    draw.rectangle([0, strip_top, W, H], fill=strip_rgb)

    # Accent lijn bovenop strip
    draw.rectangle([0, strip_top, W, strip_top + 4], fill=lighten(brand_rgb, 80))

    # Website in strip
    bbox = draw.textbbox((0, 0), website, font=f_md)
    lw   = bbox[2] - bbox[0]
    text_y = strip_top + (strip_h - (draw.textbbox((0,0), website, font=f_md)[3] - draw.textbbox((0,0), website, font=f_md)[1])) // 2
    draw.text(((W - lw) // 2, text_y), website, font=f_md, fill=white)

    return img


def generate_cta(
    output_path: Path,
    klant: str,
    rol: str,
    contact_naam: str,
    contact_tel: str,
    contact_email: str,
    website: str,
    vacature_url: str = "",
    primaire_kleur: str = "#0066CC",
    duration: int = 5,
) -> bool:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎨 CTA frame renderen via Pillow...")
    print(f"   Rol     : {rol}")
    print(f"   Klant   : {klant}")
    print(f"   Contact : {contact_naam} | {contact_tel}")
    print(f"   Kleur   : {primaire_kleur}")

    img = render_cta_image(
        klant=klant, rol=rol,
        contact_naam=contact_naam, contact_tel=contact_tel,
        contact_email=contact_email, website=website,
        primaire_kleur=primaire_kleur,
    )

    # Sla op als tijdelijke PNG
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_png = Path(tmp.name)

    img.save(tmp_png, "PNG")
    print(f"   📸 Frame opgeslagen: {tmp_png}")

    # Converteer PNG → MP4 via FFmpeg (geen drawtext nodig)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(tmp_png),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-r", "25",
        str(output_path),
    ]

    print(f"🎬 PNG → MP4 ({duration}s)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    tmp_png.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"❌ FFmpeg fout:\n{result.stderr[-800:]}")
        return False

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"   ✅ {output_path.name} ({size_mb:.1f} MB)")
    return True


def assemble_with_cta(clips: list[Path], cta_path: Path, output_path: Path) -> bool:
    all_clips = list(clips) + [cta_path]
    inputs = []
    for clip in all_clips:
        inputs += ["-i", str(clip)]

    n = len(all_clips)
    concat = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[outv]"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", concat,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        str(output_path),
    ]

    print(f"\n🔗 Assemblen: {n} clips + CTA → finale video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Assembly fout:\n{result.stderr[-800:]}")
        return False

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"   ✅ {output_path.name} ({size_mb:.1f} MB)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vacaturekanon CTA End Screen Generator")
    parser.add_argument("--klant",         required=True)
    parser.add_argument("--rol",           required=True)
    parser.add_argument("--contact",       required=True)
    parser.add_argument("--tel",           required=True)
    parser.add_argument("--email",         required=True)
    parser.add_argument("--website",       required=True)
    parser.add_argument("--vacature-url",  default="")
    parser.add_argument("--kleur",         default="#0066CC")
    parser.add_argument("--duration",      type=int, default=5)
    parser.add_argument("--output",        required=True)
    parser.add_argument("--assemble-with", nargs="+")
    parser.add_argument("--final-output")
    args = parser.parse_args()

    cta_path = Path(args.output)
    ok = generate_cta(
        output_path   = cta_path,
        klant         = args.klant,
        rol           = args.rol,
        contact_naam  = args.contact,
        contact_tel   = args.tel,
        contact_email = args.email,
        website       = args.website,
        vacature_url  = args.vacature_url,
        primaire_kleur= args.kleur,
        duration      = args.duration,
    )

    if ok and args.assemble_with and args.final_output:
        clips = [Path(c) for c in args.assemble_with]
        assemble_with_cta(clips, cta_path, Path(args.final_output))

    sys.exit(0 if ok else 1)
