#!/usr/bin/env python3
"""
kling_invideo_pipeline.py
Recruitin B.V. — TAAK 4: Kling video clips genereren via API

Gebruik:
  python3 kling_invideo_pipeline.py \
    --image ~/recruitin/meta-campaigns/assets/KT_OilGas_202603/character.png \
    --campagne KT_OilGas_202603 \
    --sector "oil & gas" \
    --duur 5 \
    --formaat 1:1

  # Auth testen:
  python3 kling_invideo_pipeline.py --test-auth

  # Dry run (geen API calls):
  python3 kling_invideo_pipeline.py --dry-run --campagne KT_OilGas_202603 --sector "oil & gas"
"""

import os, sys, time, json, requests, argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Scripts pad toevoegen aan sys.path voor lokale imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "scripts"))

# Eigen Cloud Utils
from supabase_client import upload_file
try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None

# ── Config ───────────────────────────────────────────────────────────────────
env_path = Path(__file__).resolve().parent / ".kt_env"
load_dotenv(env_path, override=True)

KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_BASE       = os.getenv("KLING_API_BASE", "https://api-singapore.klingai.com")
SLACK_URL        = os.getenv("SLACK_WEBHOOK_URL", "")
default_out      = Path(os.getenv("LOCAL_OUTPUT_BASE", "/tmp/recruitin-local"))
OUTPUT_BASE      = default_out / "meta-campaigns"

MAX_RETRIES    = 2
RETRY_WAIT     = 60   # seconden tussen retries
POLL_INTERVAL  = 15   # seconden tussen status-polls
POLL_TIMEOUT   = 900  # 15 minuten max wachttijd

# ── Sector motion prompts ─────────────────────────────────────────────────────
SECTOR_MOTION = {
    "humor": {
        "bg_hint": "factory floor, realistic natural lighting",
        "scenes": [
            "candid documentary footage, normal walking pace, the mechanic turns around with an annoyed sigh and walks out of frame, extremely realistic unposed human mechanics, natural skin, minor camera shake",
            "ultra-realistic human behavior, the mechanic sitting at the laptop heavily rubs his neck in exhaustion, wincing slightly as if having a headache from the screen, true human micro-expressions, breathing naturally",
            "subtle documentary shot, manager awkwardly adjusts the golden trash-can trophy in his hands, blinking naturally, realistic office micro-movements, no overly cinematic motion",
        ],
    },
    "oil-gas": {
        "bg_hint":   "oil refinery background, industrial pipes, flare stack, dusk lighting",
        "scenes": [
            "camera slowly zooms in, subject frustrated looking at laptop, hands on forehead, office setting",
            "camera gentle push-in, subject stands confidently arms crossed, industrial facility background",
            "camera slow pan right, subject smiling relaxed, shaking hands gesture, professional setting",
        ],
    },
    "constructie": {
        "bg_hint":   "construction site background, scaffolding, crane, building under construction",
        "scenes": [
            "camera zooms in gently, subject frustrated reviewing blueprints at desk",
            "camera slow push-in, subject authoritative arms crossed, construction site background",
            "camera soft pan, subject smiling pointing right off frame, construction background",
        ],
    },
    "automation": {
        "bg_hint":   "automation factory background, PLC panels, robotic arms, technical equipment",
        "scenes": [
            "camera gentle zoom, subject concerned looking at screens with code/diagrams",
            "camera slow push-in, subject confident arms crossed, automation equipment visible",
            "camera soft pan, subject smiling pointing right off frame, modern factory background",
        ],
    },
    "productie": {
        "bg_hint":   "production facility background, conveyor belts, industrial lighting",
        "scenes": [
            "camera gentle zoom in, subject looking worried at production floor",
            "camera slow push-in, subject confident, arms crossed, production line background",
            "camera soft pan right, subject smiling pointing off frame, factory background",
        ],
    },
    "renewable-energy": {
        "bg_hint":   "wind turbines background, solar panels, renewable energy facility",
        "scenes": [
            "camera gentle zoom, subject concerned reviewing technical drawings",
            "camera slow push-in, subject confident arms crossed, wind turbines in background",
            "camera soft pan, subject smiling pointing right, renewable energy site background",
        ],
    },
    "heijmans": {
        "bg_hint":   "large Dutch infrastructure project background, highway construction, bridge works, excavators, Heijmans-style civil engineering site, Netherlands landscape",
        "scenes": [
            "camera slowly zooms in, subject frustrated reviewing civil engineering blueprints at site office desk, hard hat on table",
            "camera gentle push-in, subject standing confidently arms crossed, large infrastructure construction site in background, safety vest",
            "camera slow pan right, subject smiling relaxed pointing right off frame, finished road or bridge in background, golden hour lighting",
        ],
    },
}

# ── Hulpfuncties ─────────────────────────────────────────────────────────────

def slack(msg: str):
    if not SLACK_URL:
        print(f"[SLACK] {msg}")
        return
    try:
        requests.post(SLACK_URL, json={"text": msg}, timeout=5)
    except Exception as e:
        print(f"[SLACK ERROR] {e}")


def sector_to_slug(sector: str) -> str:
    mapping = {
        "oil & gas": "oil-gas", "oil and gas": "oil-gas",
        "constructie": "constructie", "bouw": "constructie",
        "automation": "automation", "automatisering": "automation",
        "productie": "productie", "manufacturing": "productie",
        "renewable energy": "renewable-energy", "renewable": "renewable-energy",
        "heijmans": "heijmans", "infra": "heijmans", "gww": "heijmans",
        "civiel": "heijmans", "grond weg waterbouw": "heijmans",
    }
    return mapping.get(sector.lower().strip(), sector.lower().replace(" ", "-"))


def kling_jwt_token() -> str:
    """
    Genereert een JWT token voor Kling API authenticatie.
    Kling vereist: HS256, payload={iss: access_key, exp: now+30min, nbf: now-5s}
    """
    if pyjwt is None:
        raise ImportError("PyJWT niet geïnstalleerd — run: pip3 install PyJWT")
    now = int(time.time())
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": now + 1800,   # 30 min geldig
        "nbf": now - 5,      # 5s grace voor klokafwijking
    }
    headers = {"alg": "HS256", "typ": "JWT"}
    return pyjwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256", headers=headers)


def kling_headers() -> dict:
    return {
        "Authorization": f"Bearer {kling_jwt_token()}",
        "Content-Type":  "application/json",
    }


def image_to_base64(img_path: Path) -> str:
    import base64
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def submit_kling_job(image_path: Path, scene_prompt: str,
                     duur: int = 5, formaat: str = "1:1",
                     dry_run: bool = False) -> str | None:
    if dry_run:
        fake_id = f"dry-run-{int(time.time())}"
        print(f"   [DRY RUN] Job ingediend: {fake_id}")
        print(f"   Prompt: {scene_prompt[:80]}...")
        return fake_id

    if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
        print("   ⚠️  KLING_ACCESS_KEY/SECRET_KEY niet ingesteld — skip Kling")
        return None

    img_b64 = image_to_base64(image_path)
    payload = {
        "model_name":   "kling-v1-5",   # Pro model for superior ultra-realistic human physics
        "image":        img_b64,
        "prompt":       scene_prompt,
        "duration":     duur,
        "aspect_ratio": formaat,
        "cfg_scale":    0.5,
        "mode":         "pro",
    }

    try:
        r = requests.post(
            f"{KLING_BASE}/v1/videos/image2video",
            headers=kling_headers(),
            json=payload,
            timeout=30,
        )
        result = r.json()
        task_id = result.get("data", {}).get("task_id") or result.get("task_id")
        if task_id:
            print(f"   ✅ Kling job ingediend: {task_id}")
            return task_id
        else:
            print(f"   ❌ Kling submit fout: {result}")
            return None
    except Exception as e:
        print(f"   ❌ Kling request fout: {e}")
        return None


def poll_kling_job(task_id: str, scene_nr: int,
                   dry_run: bool = False) -> str | None:
    if dry_run:
        time.sleep(2)
        return f"https://example.com/dry-run-scene-{scene_nr:02d}.mp4"

    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        try:
            r = requests.get(
                f"{KLING_BASE}/v1/videos/image2video/{task_id}",
                headers=kling_headers(),
                timeout=15,
            )
            data = r.json().get("data", {})
            status = data.get("task_status", "")
            print(f"   ⏳ Scene {scene_nr:02d} status: {status}")

            if status == "succeed":
                videos = data.get("task_result", {}).get("videos", [])
                if videos:
                    url = videos[0].get("url")
                    print(f"   ✅ Scene {scene_nr:02d} klaar!")
                    return url
            elif status in ("failed", "error"):
                print(f"   ❌ Scene {scene_nr:02d} mislukt")
                return None
        except Exception as e:
            print(f"   ⚠️  Poll fout: {e}")

        time.sleep(POLL_INTERVAL)

    print(f"   ❌ Timeout na {POLL_TIMEOUT}s voor scene {scene_nr:02d}")
    return None


def download_video(url: str, output_path: Path, dry_run: bool = False) -> bool:
    if dry_run:
        output_path.write_text(f"[DRY RUN: {output_path.name}]")
        print(f"   [DRY RUN] Opgeslagen: {output_path}")
        return True

    try:
        r = requests.get(url, timeout=120, stream=True)
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        size_mb = output_path.stat().st_size / 1_000_000
        print(f"   💾 {output_path.name} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"   ❌ Download fout: {e}")
        return False


def schrijf_invideo_instructie(campagne_naam: str, sector: str,
                               regio: str, out_dir: Path):
    schaarste_map = {
        "oil & gas": "8.5/10", "constructie": "9.1/10",
        "automation": "9.4/10", "productie": "7.8/10",
        "renewable energy": "9.7/10",
        "heijmans": "9.2/10",
    }
    schaarste = schaarste_map.get(sector.lower(), "8+/10")

    content = f"""# InVideo Assembly Instructie
## {campagne_naam} — {sector.title()} · {regio}
## Gegenereerd: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Video bestanden

In `~/recruitin/meta-campaigns/assets/{campagne_naam}/`:
- `scene_01.mp4` — Probleem hook (gefrustreerde protagonist)
- `scene_02.mp4` — Autoriteit (zelfverzekerd)
- `scene_03.mp4` — Social proof (glimlachend)

---

## InVideo Prompt (kopieer naar Claude.ai + InVideo MCP)

```
Maak een 30-seconden Facebook Ad video voor Recruitin B.V.:

Scene 1 (0-10s): scene_01.mp4
  Tekst: "Is jouw vacature al te lang open?"
  Sfeer: urgent, herkenbaar probleem

Scene 2 (10-20s): scene_02.mp4
  Tekst: "De {sector.title()} markt staat onder druk"
  Stats: Schaarste {schaarste} | Doorlooptijd 5+ maanden gemiddeld

Scene 3 (20-30s): scene_03.mp4
  Tekst: "Gratis analyse → vacaturekanon.nl"
  CTA: oranje button (#E8630A) met pijl

Stijl: donkere achtergrond (#060708), Bricolage Grotesque font,
oranje accenten, professioneel en data-gedreven.
Formaat: exporteer 1:1 (Feed) EN 9:16 (Reels/Stories).
```

---

## Na InVideo assembly

1. Export → MP4, 1:1 en 9:16
2. Upload in Meta Ads Manager → Creative Library
3. Koppel aan campagne: **{campagne_naam}** (staat op PAUSED)
4. Controleer landing page op mobiel
5. Zet campagne op ACTIVE via Meta Business Manager
"""
    out_file = out_dir / "invideo_instructie.md"
    out_file.write_text(content, encoding="utf-8")
    print(f"   📝 InVideo instructie: {out_file}")


# ── Main ─────────────────────────────────────────────────────────────────────

def run(image_path: Path, campagne_naam: str, sector: str,
        regio: str = "Gelderland", duur: int = 5,
        formaat: str = "1:1", dry_run: bool = False) -> dict:

    slug = sector_to_slug(sector)
    motion_data = SECTOR_MOTION.get(slug, SECTOR_MOTION["productie"])
    out_dir = OUTPUT_BASE / "assets" / campagne_naam
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n── TAAK 4: Kling Video Clips ─────────────")
    print(f"   Campagne:  {campagne_naam}")
    print(f"   Sector:    {sector} → {slug}")
    print(f"   Character: {image_path}")
    print(f"   Scenes:    3 × {duur}s, {formaat}")
    print(f"   Dry run:   {'ja' if dry_run else 'nee'}")
    print()

    if not image_path.exists() and not dry_run:
        print(f"❌ Character image niet gevonden: {image_path}")
        return {}

    task_ids = []
    scenes_klaar = {}

    # ── 1. Submit alle jobs ───────────────────────────────────────────────
    print("1️⃣  Jobs indienen bij Kling...")
    for i, scene_desc in enumerate(motion_data["scenes"], start=1):
        full_prompt = (
            f"Cinematic portrait video of a confident professional man in his 40s, "
            f"dark brown neatly combed hair, light stubble beard, navy work jacket. "
            f"{scene_desc}. Background: {motion_data['bg_hint']}. "
            f"85mm lens, shallow depth of field, smooth camera motion, "
            f"no text, no watermarks, photorealistic 4K."
        )
        task_id = submit_kling_job(image_path, full_prompt, duur, formaat, dry_run)
        task_ids.append((i, task_id, full_prompt))
        time.sleep(1)

    # ── 2. Poll + download ────────────────────────────────────────────────
    print(f"\n2️⃣  Wachten op resultaten (max {POLL_TIMEOUT//60} min per scene)...")
    for scene_nr, task_id, prompt in task_ids:
        if not task_id:
            print(f"   ⚠️  Scene {scene_nr:02d} heeft geen task ID — skip")
            continue

        for attempt in range(MAX_RETRIES + 1):
            if attempt > 0:
                print(f"   🔄 Retry {attempt}/{MAX_RETRIES} voor scene {scene_nr:02d}...")
                task_id = submit_kling_job(image_path, prompt, duur, formaat, dry_run)
                if not task_id:
                    break

            video_url = poll_kling_job(task_id, scene_nr, dry_run)
            if video_url:
                out_file = out_dir / f"scene_{scene_nr:02d}.mp4"
                if download_video(video_url, out_file, dry_run):
                    scenes_klaar[f"scene_{scene_nr:02d}"] = str(out_file)
                    
                    # Cloud Backup via Supabase
                    cloud_url = upload_file(str(out_file), f"{campagne_naam}/{out_file.name}")
                    if cloud_url:
                        print(f"      [Cloud Sync] Video geüpload: {cloud_url}")
                break
            elif attempt < MAX_RETRIES:
                print(f"   ⏳ {RETRY_WAIT}s wachten...")
                time.sleep(RETRY_WAIT)

    # ── 3. InVideo instructie ─────────────────────────────────────────────
    print("\n3️⃣  InVideo instructie genereren...")
    schrijf_invideo_instructie(campagne_naam, sector, regio, out_dir)

    # ── 4. Rapport + Slack ────────────────────────────────────────────────
    rapport = {
        "campagne_naam": campagne_naam, "sector": sector,
        "scenes": scenes_klaar, "out_dir": str(out_dir),
        "timestamp": datetime.now().isoformat(), "dry_run": dry_run,
    }
    (out_dir / "kling-rapport.json").write_text(
        json.dumps(rapport, indent=2, ensure_ascii=False)
    )

    n_ok = len(scenes_klaar)
    slack(
        f"🎬 {campagne_naam} — {n_ok}/3 Kling clips klaar voor InVideo"
        if n_ok == 3 else
        f"⚠️ {campagne_naam} — Kling: {n_ok}/3 clips klaar (check logs)"
    )
    print(f"\n✅ Kling pipeline klaar — {n_ok}/3 scenes gegenereerd")
    return rapport


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recruitin Kling Video Pipeline")
    parser.add_argument("--image",     type=Path)
    parser.add_argument("--campagne",  required=True)
    parser.add_argument("--sector",    required=True)
    parser.add_argument("--regio",     default="Gelderland")
    parser.add_argument("--duur",      type=int, default=5, choices=[5, 10])
    parser.add_argument("--formaat",   default="1:1", choices=["1:1", "16:9", "9:16"])
    parser.add_argument("--dry-run",   action="store_true")
    parser.add_argument("--test-auth", action="store_true")
    args = parser.parse_args()

    if args.test_auth:
        print("🔑 Kling API auth test...")
        if not KLING_ACCESS_KEY:
            print("❌ KLING_ACCESS_KEY niet ingesteld in ~/recruitin/.env")
            sys.exit(1)
        try:
            token = kling_jwt_token()
            print(f"   JWT token: {token[:40]}...")
            r = requests.get(
                f"{KLING_BASE}/v1/videos/image2video",
                headers=kling_headers(), timeout=10
            )
            print(f"   Status: {r.status_code}")
            print(f"   Response: {r.text[:300]}")
        except Exception as e:
            print(f"❌ {e}")
        sys.exit(0)

    if not args.image:
        args.image = (
            default_out / "meta-campaigns"
            / "assets" / args.campagne / "character.png"
        )

    run(
        image_path    = args.image,
        campagne_naam = args.campagne,
        sector        = args.sector,
        regio         = args.regio,
        duur          = args.duur,
        formaat       = args.formaat,
        dry_run       = args.dry_run,
    )
