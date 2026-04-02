#!/usr/bin/env python3
"""
bts_werkenbij_beutech.py
═══════════════════════════════════════════════════════════════════════
BTS "Werken Bij Beutech" — Volledig geautomatiseerde pipeline

Wat dit script doet:
  1. Toont 6 image prompts (handmatig genereren via Antigravity/Nano Banana Pro)
  2. Genereert 6 × 10s Kling PRO video clips van de images
  3. Genereert Nederlandse voiceover per scene via ElevenLabs
  4. Assembleert alles via FFmpeg → finale 60s BTS video

Gebruik:
  # Stap 1: Genereer images (handmatig via Antigravity)
  python3 bts_werkenbij_beutech.py --show-prompts

  # Stap 2: Na image generatie, geef padden op en run volledig
  python3 bts_werkenbij_beutech.py --images-dir ./bts_images/ --run-all

  # Of stap voor stap:
  python3 bts_werkenbij_beutech.py --images-dir ./bts_images/ --voiceover-only
  python3 bts_werkenbij_beutech.py --images-dir ./bts_images/ --kling-only
  python3 bts_werkenbij_beutech.py --assemble-only

Vereisten:
  pip3 install PyJWT
  brew install ffmpeg
═══════════════════════════════════════════════════════════════════════
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Env laden ─────────────────────────────────────────────────────────────────
ENV_FILE = Path(__file__).parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

try:
    import jwt as pyjwt
except ImportError:
    sys.exit("❌  pip3 install PyJWT")

# ── Credentials ───────────────────────────────────────────────────────────────
KLING_ACCESS_KEY   = os.environ.get("KLING_ACCESS_KEY", "Aeyk3t9Re9MtTab8gG4pgfh4f3gBgQAL")
KLING_SECRET_KEY   = os.environ.get("KLING_SECRET_KEY", "RkfDrMkmmfJ4knQrkt9nYGTf3GB4f3tD")
KLING_BASE         = "https://api-singapore.klingai.com"
ELEVENLABS_KEY     = os.environ.get("ELEVENLABS_API_KEY", "sk_29d198b9baa0a2b426fd33717a2864837fc91f021908bb54")
# Adam = pNInz6obpgDQGcFmaJgB | Antoni (NL accent) = ErXwobaYiN019PkySvjV
ELEVENLABS_VOICE   = os.environ.get("ELEVENLABS_VOICE_ID", "ErXwobaYiN019PkySvjV")

OUTPUT_BASE = Path(os.environ.get("OUTPUT_DIR",
    "/Users/wouterarts/Library/CloudStorage/OneDrive-Gedeeldebibliotheken-Recruitin"
    "/output/vacaturekanon/test-videos")) / "beutech_bts_werkenbij"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

# ── Negatief prompt (Kling) ────────────────────────────────────────────────────
NEG = (
    "slow motion, time-lapse, claymation, puppet movement, robotic stiff movement, "
    "morphing face, melting skin, dissolving features, warping, jitter, flickering, "
    "floating hands, extra limbs, deformed anatomy, text, watermark, logo, CGI look"
)

# ════════════════════════════════════════════════════════════════════════════════
#  6 SCENES — Image prompts + Motion prompts + Nederlandse voiceover
# ════════════════════════════════════════════════════════════════════════════════

SCENES = [
    {
        "id":    "01_aankomst",
        "title": "Aankomst",

        # ── IMAGE PROMPT (gebruik in Antigravity / Nano Banana Pro) ──────────
        "image_prompt": (
            "35mm lens, f/2.8, slightly wide angle. Documentary workplace photography, "
            "candid, unposed. Shot on Sony A7IV. Photorealistic 8K. "
            "Two Dutch male factory workers arriving at the entrance of a modern plastics "
            "manufacturing plant in the early morning — warm amber sunrise light on the "
            "building facade. One man (mid-30s, short dark hair, red Beutech t-shirt, dark "
            "work trousers, safety shoes) holds a coffee thermos and looks at his colleague "
            "with a relaxed morning smile. The other (early 40s, stocky, slight stubble, "
            "red t-shirt, dark trousers) gestures casually with one hand — mid-sentence. "
            "Body language: loose, unhurried, familiar — these two know each other well. "
            "The factory entrance: large sliding steel door half-open, yellow safety "
            "markings on the floor, Beutech signage (no readable text). Morning mist "
            "catches the warm light. One other worker visible inside, already moving. "
            "No text, no watermark, no logos."
        ),

        # ── MOTION PROMPT (Kling — per 2.5s blok) ────────────────────────────
        "motion_prompt": (
            # 0–2.5s
            "The man with the coffee thermos raises it to his lips and takes a small sip — "
            "wrist rotates naturally, elbow bends. His head tilts back 5 degrees as he drinks, "
            "then returns level. His eyes stay on his colleague, eyebrows slightly raised — "
            "listening mode. "
            # 2.5–5s
            "The other man finishes his gesture — hand drops naturally to his side, weight "
            "shifts from right foot to left foot, hip drops 2 cm. He nods once — small chin-down "
            "chin-up movement — and smiles. Both breathe visibly at normal conversation pace. "
            # 5–7.5s
            "The man with the thermos responds — his head turns slightly left toward the entrance, "
            "then back to his colleague. He takes one step forward. The other man follows, "
            "shoulder turning naturally as he pivots. "
            # 7.5–10s
            "Both walk toward the open factory door — natural walking gait, arms swinging "
            "slightly, the thermos held loosely. Morning light catches their red t-shirts. "
            "Camera completely static on tripod. Real-time speed. No slow motion."
        ),

        # ── VOICEOVER ─────────────────────────────────────────────────────────
        "voiceover": (
            "Elke ochtend begint het hier. "
            "Met dezelfde mensen. En dat voelt gewoon goed."
        ),
        "vo_duration": 5.0,
    },
    {
        "id":    "02_vakwerk_cnc",
        "title": "Vakwerk CNC",

        "image_prompt": (
            "85mm portrait lens, f/1.8, perfectly sharp subject, deep bokeh background. "
            "Documentary photography, candid, unposed. Shot on Sony A7IV Zeiss 85mm. "
            "Photorealistic 8K. "
            "Dutch male CNC operator, early 30s, clean-shaved with a day's stubble, "
            "focused concentration expression — the involuntary furrow of the brow of someone "
            "doing precise work. Red Beutech t-shirt, dark navy work trousers. "
            "He leans slightly forward over a steel workbench, right hand holding a digital "
            "vernier caliper measuring a freshly machined thick-walled grey PE pipe section. "
            "Left hand steadies the pipe. His eyes are on the caliper readout — total absorption. "
            "The measurement is critical. "
            "Background (soft bokeh): Hembrug CNC lathe, stacks of black PE material on a pallet, "
            "yellow overhead crane rail, warm late-morning factory light through high skylights. "
            "No text, no watermark, no logos."
        ),

        "motion_prompt": (
            # 0–2.5s
            "His chest rises slowly with a focused inhale — held briefly. "
            "His right hand adjusts the caliper jaw by 1mm — a tiny wrist micro-movement. "
            "His eyes drop to the readout, brow furrows slightly. "
            # 2.5–5s
            "He reads the measurement. His lips press together in a slight nod — "
            "chin drops then rises: 'within tolerance.' A micro-expression of quiet satisfaction "
            "— eyebrows relax, jaw unclenches. "
            # 5–7.5s
            "He sets the caliper down on the workbench — deliberate, careful. "
            "He lifts the PE pipe section slightly, rotates it 45 degrees to inspect the end face. "
            "His head tilts right at the neck to get a better angle. "
            # 7.5–10s
            "He nods once — decisive — and places the part back. "
            "He glances up toward someone off-camera: a brief natural eye-contact moment. "
            "Relaxed exhale, shoulders drop slightly. "
            "Camera completely static. Real-time speed."
        ),

        "voiceover": (
            "Bij Beutech draait het om vakmanschap. "
            "Jij bent degene die bepaalt of een product goed genoeg is."
        ),
        "vo_duration": 5.5,
    },
    {
        "id":    "03_koffiepauze",
        "title": "Koffiepauze",

        "image_prompt": (
            "35mm lens, f/2.8, slightly wide. Documentary, candid, unposed. "
            "Shot on Sony A7IV. Photorealistic 8K. "
            "Three Dutch male factory workers at a coffee machine in a bright factory break "
            "area — mid-morning break. All wearing red Beutech t-shirts and dark work trousers. "
            "Ages: late 20s (slim, arm sleeve tattoo visible), mid-30s (glasses, slightly taller), "
            "early 40s (stocky, warm smile). One of them just said something genuinely funny — "
            "the tattooed man is laughing with his head tilted back slightly, the man with "
            "glasses is grinning sideways, the stocky man holds his coffee cup near his mouth "
            "trying not to spill while laughing. "
            "The break area: clean, functional, good natural light from a high window. "
            "A notice board visible in background (no readable text). Coffee machine: modern "
            "stainless steel. Steel table. Blue/grey industrial chairs. "
            "No text, no watermark, no logos."
        ),

        "motion_prompt": (
            # 0–2.5s
            "The tattooed man's laughter subsides — he straightens, wipes outer corner "
            "of his eye with his knuckle, shakes his head slightly side to side (still smiling). "
            "The man with glasses takes a sip of coffee, still grinning with his eyes. "
            # 2.5–5s
            "The stocky man carefully lowers his coffee cup — the near-spill moment has passed. "
            "He points at the tattooed man with one finger in a 'that was your fault' gesture, "
            "grinning. All three breathe at relaxed conversation pace. "
            # 5–7.5s
            "The tattooed man raises both hands briefly — 'guilty!' — a natural open-palm "
            "shoulder shrug. The glasses man looks between the two, still smiling. "
            "Small postural weight shifts as they settle into easier stances. "
            # 7.5–10s
            "A natural pause in laughter — they sip their coffees. Comfortable silence for "
            "half a second. The stocky man looks toward the factory floor and nods once — "
            "time to go back. Camera locked. Real-time."
        ),

        "voiceover": (
            "De pauze duurt tien minuten. "
            "Maar reden waarom je hier wil werken, die snap je in vijf."
        ),
        "vo_duration": 5.5,
    },
    {
        "id":    "04_samen_tillen",
        "title": "Samen tillen",

        "image_prompt": (
            "35mm lens, f/2.8, low angle looking slightly up. Documentary, candid, unposed. "
            "Shot on Sony A7IV. Photorealistic 8K. "
            "Two Dutch male factory workers lifting a large black PE polyethylene drainage "
            "chamber (cylindrical, approximately 1.2m tall, 600mm diameter) together in a "
            "factory workshop. Both wear red Beutech t-shirts and dark work trousers with "
            "safety shoes. "
            "The man on the left (mid-30s, beard stubble) grips the lower rim with both hands, "
            "knees slightly bent — proper lifting posture, core engaged. Mild exertion visible "
            "in his expression: focused, slight eye squint, jaw set. "
            "The man on the right (early 40s, clean-shaved) grips the opposite side, "
            "his gaze meets the other man's — silent coordination. "
            "The heavy black PE tank is mid-air, 30cm off the factory floor. "
            "Background: CNC machines, large PE material stock on pallets, yellow crane rail. "
            "Factory floor: polished grey epoxy. Warm LED factory light overhead. "
            "No text, no watermark, no logos."
        ),

        "motion_prompt": (
            # 0–2.5s
            "Both men's arms tense as they lift — natural muscle engagement visible in "
            "forearms and upper arms. Their knees straighten as the PE chamber rises. "
            "The left man's head is bowed slightly from effort, then rises. "
            # 2.5–5s
            "They carry it 3 steps to the right — short controlled steps, weight shifting "
            "with each step. Their faces show calm focused exertion — not struggle, "
            "but real physical effort. "
            # 5–7.5s
            "They begin to lower it: knees bend again, backs straight. "
            "The right man glances down at the floor to guide the placement. "
            "The left man matches his movement — their eyes meet briefly for sync. "
            # 7.5–10s
            "The tank touches down. Both men straighten, hands release. "
            "The left man rolls one shoulder back — a small post-lift release movement. "
            "The right man nods once: done. A brief shared look — quiet teamwork. "
            "Camera static, real-time."
        ),

        "voiceover": (
            "Sommige dingen doe je niet alleen. "
            "Gelukkig hoef je dat bij Beutech ook nooit."
        ),
        "vo_duration": 5.0,
    },
    {
        "id":    "05_einde_dag",
        "title": "Einde van de dag",

        "image_prompt": (
            "50mm lens, f/2.2. Documentary, candid, unposed. Sony A7IV. Photorealistic 8K. "
            "Dutch male factory worker, mid-30s, sleeve tattoo, end of workday — standing at "
            "a deep sink washing his hands. Red Beutech t-shirt, dark work trousers. "
            "He looks out a small factory window while washing — not at camera. "
            "Expression: calm, satisfied, a slight upward curve at the corners of his mouth. "
            "The kind of tired that feels earned. "
            "Warm late-afternoon golden light through the window catches his profile and "
            "the water streaming over his hands. "
            "Behind him: coat hooks with jackets, other workers in the background changing "
            "or putting on civilian clothes. "
            "No text, no watermark, no logos."
        ),

        "motion_prompt": (
            # 0–2.5s
            "His hands move naturally under the water — rubbing palms together, thumb over "
            "knuckles, the automatic motion of someone who has done this a thousand times. "
            "He continues to look out the window, eyes relaxed and slightly unfocused. "
            # 2.5–5s
            "He glances down at his hands briefly, then back up to the window. "
            "A slow, full exhale — chest falls visibly. His shoulders drop 2cm. "
            "The day is done. "
            # 5–7.5s
            "He turns off the tap — a simple wrist movement. "
            "Reaches for a paper towel with his right hand. "
            "His head turns slightly toward the sound of colleagues talking in background. "
            # 7.5–10s
            "He dries his hands, crumples the towel, tosses it. "
            "Turns toward the exit — a relaxed, easy movement. "
            "A small natural smile as he passes a colleague. Camera static, real-time."
        ),

        "voiceover": (
            "Aan het einde van de dag weet je precies wat je gedaan hebt. "
            "En dat gevoel... dat neem je mee naar huis."
        ),
        "vo_duration": 6.0,
    },
    {
        "id":    "06_blooper",
        "title": "De blooper",

        "image_prompt": (
            "35mm lens, f/2.8, slightly wide. Documentary, candid — this looks like it was "
            "accidentally filmed. Sony A7IV. Photorealistic 8K. "
            "Two Dutch male factory workers in red Beutech t-shirts and dark work trousers "
            "next to a large black PE drainage chamber on the factory floor. "
            "The taller one (early 30s, slim, tattoo on left arm) has just tried to move "
            "the tank alone — and clearly overestimated himself. He stands with his arms "
            "around the tank, slightly red-faced, the tank barely budged. "
            "The other worker (early 40s, stocky, stubble) stands 2 meters away with his "
            "coffee cup — he witnessed the whole thing — and is now laughing WITH his whole "
            "body: head back, one hand on his belly, coffee held safely out to the side. "
            "The tall man has turned to face him, arms spread in a 'help me?' gesture, "
            "starting to laugh at himself too. "
            "The moment is completely genuine — pure factory floor humour. "
            "Background: normal factory floor, CNC machines, yellow crane. "
            "No text, no watermark, no logos."
        ),

        "motion_prompt": (
            # 0–2.5s
            "The tall man still has his arms around the tank — he looks at the stocky man, "
            "realizes the futility, and lets go. His arms drop to his sides. "
            "A beat of silence — then his face breaks into a grin. "
            # 2.5–5s
            "The stocky man's laugh continues — he waves his free hand in a 'I told you so' "
            "gesture, head shaking side to side. His coffee cup wobbles but stays safe. "
            "The tall man raises one hand and points at the tank as if to blame it. "
            # 5–7.5s
            "Both men are now laughing openly. The tall man runs one hand over his hair — "
            "the universal 'that was dumb' self-aware gesture. "
            "The stocky man takes a step forward to finally help. "
            # 7.5–10s
            "The stocky man hands the tall man his coffee cup to hold. "
            "He crouches to the tank to show the proper grip technique — a 'watch and learn' "
            "moment. The tall man watches, still grinning. Camera static, real-time."
        ),

        "voiceover": (
            "En soms... gaat het even niet zoals gepland. "
            "Geen probleem. Er is altijd iemand die wel even wil helpen."
        ),
        "vo_duration": 5.5,
    },
]


# ════════════════════════════════════════════════════════════════════════════════
#  STAP 1 — Toon image prompts
# ════════════════════════════════════════════════════════════════════════════════

def show_prompts():
    print("\n" + "═" * 70)
    print("  BTS WERKENBIJ BEUTECH — Image Prompts voor Nano Banana Pro")
    print("═" * 70)
    for s in SCENES:
        print(f"\n{'─'*70}")
        print(f"  SCENE {s['id']} — {s['title'].upper()}")
        print(f"{'─'*70}")
        print(s["image_prompt"])
    print(f"\n{'═'*70}")
    print("  Genereer elke image via Antigravity en sla op als:")
    for s in SCENES:
        print(f"  → bts_images/{s['id']}.png")
    print("═" * 70 + "\n")


# ════════════════════════════════════════════════════════════════════════════════
#  STAP 2 — ElevenLabs voiceover
# ════════════════════════════════════════════════════════════════════════════════

def generate_voiceover(scene: dict, out_dir: Path) -> Path | None:
    out_path = out_dir / f"{scene['id']}_vo.mp3"
    if out_path.exists():
        print(f"  ⏩ Voiceover al aanwezig: {out_path.name}")
        return out_path

    print(f"  🎙️  ElevenLabs: {scene['title']}...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}"
    payload = json.dumps({
        "text": scene["voiceover"],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.80,
            "style": 0.20,
            "use_speaker_boost": True,
        },
    }).encode()
    headers = {
        "xi-api-key": ELEVENLABS_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out_path.write_bytes(r.read())
        size = out_path.stat().st_size // 1024
        print(f"  ✓ {out_path.name} ({size} KB)")
        return out_path
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ✗ ElevenLabs HTTP {e.code}: {body[:200]}")
        return None


# ════════════════════════════════════════════════════════════════════════════════
#  STAP 3 — Kling image-to-video
# ════════════════════════════════════════════════════════════════════════════════

def make_jwt():
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5,
    }
    return pyjwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256")


def kling_api(method: str, path: str, payload: dict | None = None):
    url = f"{KLING_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {make_jwt()}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:300]}")
        return None


def submit_kling(scene: dict, image_path: Path) -> str | None:
    print(f"  🎬 Kling submit: {scene['title']}...")
    img_b64 = base64.b64encode(image_path.read_bytes()).decode()
    payload = {
        "model_name": "kling-v1-6",
        "mode":        "pro",
        "duration":    "10",
        "aspect_ratio":"9:16",
        "image":       img_b64,
        "prompt":      scene["motion_prompt"],
        "negative_prompt": NEG,
        "cfg_scale":   0.25,
    }
    r = kling_api("POST", "/v1/videos/image2video", payload)
    if r and r.get("code") == 0:
        tid = r["data"]["task_id"]
        print(f"  ✓ Task ID: {tid}")
        return tid
    print(f"  ✗ Submit mislukt: {r}")
    return None


def poll_kling(task_id: str, name: str, out_dir: Path, timeout=900) -> Path | None:
    out_path = out_dir / f"{name}_raw.mp4"
    start = time.time()
    while time.time() - start < timeout:
        r = kling_api("GET", f"/v1/videos/image2video/{task_id}", {})
        if not r:
            time.sleep(20)
            continue
        status = r.get("data", {}).get("task_status", "")
        if status == "succeed":
            url = r["data"]["task_result"]["videos"][0]["url"]
            urllib.request.urlretrieve(url, out_path)
            size = out_path.stat().st_size // 1024
            print(f"  ✓ {out_path.name} ({size} KB)")
            return out_path
        elif status == "failed":
            print(f"  ✗ FAILED: {r['data'].get('task_status_msg', '?')}")
            return None
        elapsed = int(time.time() - start)
        print(f"  [{name}] {status} ({elapsed}s)...")
        time.sleep(20)
    print(f"  ✗ Timeout: {name}")
    return None


# ════════════════════════════════════════════════════════════════════════════════
#  STAP 4 — FFmpeg: voiceover + video mergen per scene, dan alles concat
# ════════════════════════════════════════════════════════════════════════════════

def merge_vo_video(video_path: Path, vo_path: Path, out_path: Path) -> bool:
    """Merge voiceover MP3 op video clip. VO wordt gefadet na xx seconden."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(vo_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",                # stop at shortest stream (video = 10s)
        "-af", "afade=t=out:st=8.5:d=1.5",  # fade out VO laatste 1.5s
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  ✓ Merged: {out_path.name}")
        return True
    print(f"  ✗ FFmpeg merge fout: {r.stderr[-200:]}")
    return False


def assemble_final(merged_clips: list[Path], out_dir: Path) -> Path | None:
    """Concat alle merged clips tot finale BTS video."""
    list_f = out_dir / "concat_final.txt"
    list_f.write_text("\n".join(f"file '{c}'" for c in merged_clips if c and c.exists()))

    final = out_dir / "beutech_bts_werkenbij_FINAL.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_f),
        "-c:v", "libx264", "-c:a", "aac",
        "-preset", "fast",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        str(final),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and final.exists():
        mb = final.stat().st_size // (1024 * 1024)
        print(f"\n  ✅ FINALE VIDEO: {final.name} ({mb} MB)")
        subprocess.run(["open", str(final)])
        return final
    print(f"  ✗ Assembly fout: {r.stderr[-300:]}")
    return None


# ════════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="BTS Werken Bij Beutech — volledige video pipeline"
    )
    parser.add_argument("--show-prompts",   action="store_true",
                        help="Toon alle image prompts (gebruik in Antigravity)")
    parser.add_argument("--images-dir",     type=Path, default=None,
                        help="Map met de 6 gegenereerde BTS images (PNG)")
    parser.add_argument("--voiceover-only", action="store_true",
                        help="Alleen voiceover genereren")
    parser.add_argument("--kling-only",     action="store_true",
                        help="Alleen Kling video clips genereren")
    parser.add_argument("--assemble-only",  action="store_true",
                        help="Alleen finaal assemblageren (clips + VO al aanwezig)")
    parser.add_argument("--run-all",        action="store_true",
                        help="Volledige pipeline: voiceover + Kling + assembly")
    args = parser.parse_args()

    if args.show_prompts:
        show_prompts()
        return

    vo_dir    = OUTPUT_BASE / "voiceover"
    clip_dir  = OUTPUT_BASE / "clips"
    merged_dir = OUTPUT_BASE / "merged"
    for d in [vo_dir, clip_dir, merged_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # ── Voiceover ──────────────────────────────────────────────────────────────
    if args.voiceover_only or args.run_all:
        print("\n" + "═" * 60)
        print("  STAP 1 — Voiceover genereren (ElevenLabs)")
        print("═" * 60)
        for scene in SCENES:
            generate_voiceover(scene, vo_dir)
            time.sleep(1)

    # ── Kling ──────────────────────────────────────────────────────────────────
    if args.kling_only or args.run_all:
        if not args.images_dir:
            sys.exit("❌  Geef --images-dir op (map met de 6 PNG images)")
        images_dir = args.images_dir

        print("\n" + "═" * 60)
        print("  STAP 2 — Kling video clips genereren")
        print("═" * 60)

        tasks = {}
        for scene in SCENES:
            img = images_dir / f"{scene['id']}.png"
            if not img.exists():
                print(f"  ⚠️  Niet gevonden: {img} — skip")
                continue
            tid = submit_kling(scene, img)
            if tid:
                tasks[scene["id"]] = tid
            time.sleep(3)

        print(f"\n  {len(tasks)}/{len(SCENES)} jobs ingediend — polling...\n")

        for scene in SCENES:
            sid = scene["id"]
            if sid not in tasks:
                continue
            clip_path = clip_dir / f"{sid}_raw.mp4"
            if clip_path.exists():
                print(f"  ⏩ Clip al aanwezig: {clip_path.name}")
                continue
            poll_kling(tasks[sid], sid, clip_dir)

    # ── Assembly ───────────────────────────────────────────────────────────────
    if args.assemble_only or args.run_all:
        print("\n" + "═" * 60)
        print("  STAP 3 — Merge voiceover + video per scene")
        print("═" * 60)
        merged_clips = []
        for scene in SCENES:
            sid = scene["id"]
            raw   = clip_dir  / f"{sid}_raw.mp4"
            vo    = vo_dir    / f"{sid}_vo.mp3"
            out   = merged_dir / f"{sid}_merged.mp4"
            if not raw.exists():
                print(f"  ⚠️  Clip ontbreekt: {raw.name}")
                continue
            if out.exists():
                print(f"  ⏩ Merged al aanwezig: {out.name}")
                merged_clips.append(out)
                continue
            if vo.exists():
                if merge_vo_video(raw, vo, out):
                    merged_clips.append(out)
            else:
                print(f"  ⚠️  Geen VO voor {sid} — clip zonder audio")
                merged_clips.append(raw)

        print("\n" + "═" * 60)
        print("  STAP 4 — Finale assembly")
        print("═" * 60)
        assemble_final(merged_clips, OUTPUT_BASE)


if __name__ == "__main__":
    main()
