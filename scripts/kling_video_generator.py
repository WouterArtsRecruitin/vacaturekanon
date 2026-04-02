#!/usr/bin/env python3
"""
kling_video_generator.py — Recruitin B.V.
KlingVideoGenerator class met correcte JWT authenticatie (HS256).

Ondersteunt:
  - text2video  → shortvideo zonder character image
  - image2video → pipeline clips met character image

Gebruik:
  from kling_video_generator import KlingVideoGenerator, HEIJMANS_SCENES
  gen = KlingVideoGenerator()
  results = gen.generate_batch(HEIJMANS_SCENES)
"""

import os, sys, time, json, base64, requests
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

try:
    import jwt as pyjwt
except ImportError:
    raise ImportError("PyJWT niet geïnstalleerd — run: pip3 install PyJWT")

# ── Config ────────────────────────────────────────────────────────────────────
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path, override=True)

KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_BASE       = os.getenv("KLING_API_BASE", "https://api-singapore.klingai.com")

# ── Heijmans config ───────────────────────────────────────────────────────────
HEIJMANS_CONFIG = {
    "client":  "Heijmans N.V.",
    "project": "Senior Uitvoerder Wegen",
    "kling": {
        "model":        "kling-v2-6",
        "aspect_ratio": "9:16",
        "mode":         "std",
        "cfg_scale":    0.5,
    },
}

# Heijmans Option B — 5 scenes (tekst/logo via Canva, niet via Kling)
# Bron: KLING_PROMPTS_5SCENES.md
HEIJMANS_SCENES = {
    "B1_early_arrival": {
        "type":     "text2video",
        "duration": 3,
        "prompt": (
            "Authentic documentary footage: Senior construction worker (age 45-50, real person "
            "aesthetic, NOT model) arriving at Heijmans construction site early morning, "
            "approximately 06:45-07:00. Worker cycling or parking car, carrying bag/equipment, "
            "casual but professional deportment. Yellow safety vest visible, construction worker "
            "attire authentic. Site entrance visible, temporary fencing, morning light quality "
            "Dutch landscape. Candid moment, no awareness of camera, natural arrival routine "
            "captured. Camera: Medium distance, slight panning following arrival motion. "
            "Lighting: Early morning golden light, natural Dutch spring weather, soft shadows. "
            "Motion: Natural walking/cycling rhythm, authentic arrival energy. "
            "Style: Documentary authenticity, hyperrealistic human movement. "
            "No text, no watermarks, no logos."
        ),
    },
    "B2_team_briefing": {
        "type":     "text2video",
        "duration": 5,
        "prompt": (
            "Documentary footage: Daily standup crew briefing on active construction site, "
            "approximately 07:00-07:30. Same worker (from B1) conducting briefing with 10-12 "
            "authentic crew members. Workers gathered around construction plans/blueprint, real "
            "work discussion visible. Hands on plans, pointing, discussing specific work tasks. "
            "Natural conversation captured. Occasional laughter, genuine professional interaction, "
            "SHORT hierarchical distance. Yellow safety vests prominent, site setup authentic. "
            "Camera: Medium-close shot, slight observational movement, documentary framing. "
            "Lighting: Early morning site light, natural shadows, warm professional ambience. "
            "Color: Yellow and navy accents, earthy construction colors dominant. "
            "Style: Hyperrealistic human interaction, authentic construction context. "
            "No text, no watermarks, no logos."
        ),
    },
    "B3_technical_work": {
        "type":     "text2video",
        "duration": 5,
        "prompt": (
            "Close-up documentary footage: Technical work moment on construction site, "
            "approximately 10:30-11:00. Same worker + colleague checking drainage systems, "
            "measuring, examining foundation specifications per RAW contract. "
            "Close-up: Hands visible with measuring tools, technical drawings, real "
            "problem-solving in action. Shallow DOF: Hands and technical detail in sharp focus, "
            "background site blurred. Precision visible: Professional competence, careful "
            "measurement, technical accuracy. NO dramatization: Pure technical work "
            "documentation, authentic construction problem-solving. "
            "Camera: Close macro perspective, shallow DOF, technical detail-focused. "
            "Lighting: Site lighting on technical work, natural shadows. "
            "Style: Hyperrealistic hands-on technical work, authentic precision visible. "
            "No text, no watermarks, no logos."
        ),
    },
    "B4_culture_moment": {
        "type":     "text2video",
        "duration": 3,
        "prompt": (
            "Candid documentary footage: Construction crew lunch/break moment, approximately "
            "12:30-13:00. Multiple workers (same crew from earlier scenes) in casual "
            "conversation, natural laughter. Site lunch setup (temporary lunch area/tent), "
            "genuine human interaction, NO forced smiles. Casual collegial atmosphere: "
            "Hands on shoulders, friendly gestures, real team dynamic. Workers of varying "
            "ages/experience: Realistic diversity, authentic blue-collar culture. "
            "Yellow vests visible but secondary to human interaction focus. "
            "Camera: Medium distance, observational documentary style, capturing genuine moments. "
            "Lighting: Soft natural light, warm lunch area illumination, human-focused. "
            "Style: Hyperrealistic candid human moment, authentic team interaction. "
            "No text, no watermarks, no logos."
        ),
    },
    # B5 = closing frame met Heijmans logo + tekst → NIET via Kling, maar via Canva/InVideo
    # Voeg B5 handmatig toe als branded slide in InVideo assembly stap.
}

# ── Werkvoorbereider Wegen BTS — v3 (correcte Heijmans werkkleding op basis van referentiefoto's) ──
# Heijmans werkkleding (exact, op basis van referentiefoto's):
#   - Fel ORANJE hi-vis jas (volledige jas, NIET hesje, NIET geel-groen)
#   - Zilveren reflectiestrepen op jas
#   - Witte veiligheidshelm (leiding) of gele helm (veld)
#   - Donkere broek (zwart/donkergrijs) of jeans
#   - Sommige veldwerkers: volledig oranje overall/werkpak
#   - Vies, modderig, versleten — echt gebruikt
# Heijmans site: oranje banners op hekwerk, gele machines, plat polderlandschap, modder
# Kling kan geen logo/tekst renderen → branding via InVideo/Canva achteraf

_HEIJMANS_WORKWEAR = (
    "bright orange high-visibility full jacket with silver reflective horizontal stripes, "
    "yellow safety hard hat, dark trousers or jeans, safety boots covered in mud. "
    "The orange jacket is the dominant visual — vivid construction orange, not yellow or green. "
    "Clothing looks used, weathered, muddy — authentic work site condition, NOT clean or new."
)

_SENIOR_BODY_LANGUAGE = (
    "This man is a senior site director responsible for 8 million euro infrastructure projects. "
    "He moves with absolute confidence and authority — deliberate steady stride, upright posture, "
    "commanding presence. He knows every detail of this site. His gestures are decisive and precise, "
    "not hesitant. Experienced craftsman leadership energy, decades of expertise visible in every movement."
)

_HEIJMANS_SITE = (
    "Active Dutch highway road construction site, flat polder landscape with green fields, "
    "grey overcast sky, asphalt paving machine in operation, yellow excavators, "
    "orange site fencing panels along the road, red-white chevron barriers, "
    "orange temporary road signs, fresh black asphalt being laid, "
    "muddy brown clay ground alongside the road, puddles."
)

WERKVOORBEREIDER_A = {
    "A1_briefing": {
        "type":     "text2video",
        "duration": 10,
        "model":    "kling-v2-6",
        "mode":     "std",
        "prompt": (
            f"Documentary footage: Senior Dutch infrastructure site director (male, 50s, grey beard, "
            f"weathered face, tanned) confidently reviewing engineering drawings on a site table. "
            f"Wearing: {_HEIJMANS_WORKWEAR} "
            f"{_SENIOR_BODY_LANGUAGE} "
            f"He points decisively at the plan, looks up at the road works with a knowing expression, "
            f"nods firmly. Every movement shows complete command of the project. "
            f"Background: {_HEIJMANS_SITE} "
            f"Camera: medium shot, steady observational documentary. "
            f"Lighting: overcast grey Dutch daylight, flat natural light. "
            f"No text, no watermarks, no logos. Photorealistic 4K."
        ),
    },
    "A2_inspection": {
        "type":     "text2video",
        "duration": 10,
        "model":    "kling-v2-6",
        "mode":     "std",
        "prompt": (
            f"Documentary footage: Senior Dutch infrastructure site director (male, 50s, grey beard) "
            f"walking with confident steady stride along freshly laid asphalt, inspecting road quality. "
            f"Wearing: {_HEIJMANS_WORKWEAR} "
            f"{_SENIOR_BODY_LANGUAGE} "
            f"He walks with purpose — hands behind back surveying the work, then crouches to check "
            f"the surface, stands back up decisively. Owns the entire site with his presence. "
            f"Background: {_HEIJMANS_SITE} "
            f"Camera: follow-shot from slight distance, documentary style. "
            f"Lighting: grey Dutch overcast, flat natural light, muddy reflections. "
            f"No text, no watermarks, no logos. Photorealistic 4K."
        ),
    },
    "A3_conversation": {
        "type":     "text2video",
        "duration": 10,
        "model":    "kling-v2-6",
        "mode":     "std",
        "prompt": (
            f"Documentary footage: Senior Dutch infrastructure site director (male, 50s, grey beard) "
            f"giving clear instructions to two younger colleagues in orange jackets at the site. "
            f"All wearing: {_HEIJMANS_WORKWEAR} "
            f"{_SENIOR_BODY_LANGUAGE} "
            f"He points authoritatively toward the road ahead, colleagues listen attentively. "
            f"He gestures at construction plans on a table, explaining with decisive hand movements. "
            f"Clear hierarchy — he is in charge and everyone knows it. "
            f"Background: {_HEIJMANS_SITE} "
            f"Camera: medium two-shot, observational documentary. "
            f"Lighting: overcast Dutch daylight, even soft light. "
            f"No text, no watermarks, no logos. Photorealistic 4K."
        ),
    },
}

# ── Werkvoorbereider BTS — Variant B (kling-v1.5 pro, hogere motion quality) ──
WERKVOORBEREIDER_B = {
    "B1_briefing": {
        "type":     "text2video",
        "duration": 10,
        "model":    "kling-v1-5",
        "mode":     "pro",
        "prompt": (
            f"Documentary footage: Senior Dutch infrastructure site director (male, 50s, grey beard, "
            f"weathered face, tanned) confidently reviewing engineering drawings on a site table. "
            f"Wearing: {_HEIJMANS_WORKWEAR} "
            f"{_SENIOR_BODY_LANGUAGE} "
            f"He points decisively at the plan, looks up at the road works with a knowing expression, "
            f"nods firmly. Every movement shows complete command of the project. "
            f"Background: {_HEIJMANS_SITE} "
            f"Camera: medium shot, steady observational documentary. "
            f"Lighting: overcast grey Dutch daylight, flat natural light. "
            f"No text, no watermarks, no logos. Photorealistic 4K."
        ),
    },
    "B2_inspection": {
        "type":     "text2video",
        "duration": 10,
        "model":    "kling-v1-5",
        "mode":     "pro",
        "prompt": (
            f"Documentary footage: Senior Dutch infrastructure site director (male, 50s, grey beard) "
            f"walking with confident steady stride along freshly laid asphalt, inspecting road quality. "
            f"Wearing: {_HEIJMANS_WORKWEAR} "
            f"{_SENIOR_BODY_LANGUAGE} "
            f"He walks with purpose — hands behind back surveying the work, then crouches to check "
            f"the surface, stands back up decisively. Owns the entire site with his presence. "
            f"Background: {_HEIJMANS_SITE} "
            f"Camera: follow-shot from slight distance, documentary style. "
            f"Lighting: grey Dutch overcast, flat natural light, muddy reflections. "
            f"No text, no watermarks, no logos. Photorealistic 4K."
        ),
    },
    "B3_conversation": {
        "type":     "text2video",
        "duration": 10,
        "model":    "kling-v1-5",
        "mode":     "pro",
        "prompt": (
            f"Documentary footage: Senior Dutch infrastructure site director (male, 50s, grey beard) "
            f"giving clear instructions to two younger colleagues in orange jackets at the site. "
            f"All wearing: {_HEIJMANS_WORKWEAR} "
            f"{_SENIOR_BODY_LANGUAGE} "
            f"He points authoritatively toward the road ahead, colleagues listen attentively. "
            f"He gestures at construction plans on a table, explaining with decisive hand movements. "
            f"Clear hierarchy — he is in charge and everyone knows it. "
            f"Background: {_HEIJMANS_SITE} "
            f"Camera: medium two-shot, observational documentary. "
            f"Lighting: overcast Dutch daylight, even soft light. "
            f"No text, no watermarks, no logos. Photorealistic 4K."
        ),
    },
}

# Legacy single-scene (voor backward compat)
WERKVOORBEREIDER_SCENES = WERKVOORBEREIDER_A


# ── KlingVideoGenerator ───────────────────────────────────────────────────────

class KlingVideoGenerator:
    """
    Kling AI video generator met JWT authenticatie (HS256).
    Ondersteunt text2video en image2video.
    """

    def __init__(self,
                 access_key: str = "",
                 secret_key: str = "",
                 base_url: str = ""):
        self.access_key = access_key or KLING_ACCESS_KEY
        self.secret_key = secret_key or KLING_SECRET_KEY
        self.base_url   = (base_url or KLING_BASE).rstrip("/")

        if not self.access_key or not self.secret_key:
            raise ValueError(
                "KLING_ACCESS_KEY en KLING_SECRET_KEY vereist. "
                "Stel in via ~/recruitin/.env of geef door als argument."
            )

        self.tasks: dict = {}
        self.log: list   = []

    # ── JWT ──────────────────────────────────────────────────────────────────

    def _jwt_token(self) -> str:
        """Genereer HS256 JWT — Kling vereist iss=access_key, exp+30min, nbf-5s."""
        now = int(time.time())
        payload = {
            "iss": self.access_key,
            "exp": now + 1800,
            "nbf": now - 5,
        }
        return pyjwt.encode(
            payload, self.secret_key,
            algorithm="HS256",
            headers={"alg": "HS256", "typ": "JWT"},
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._jwt_token()}",
            "Content-Type":  "application/json",
        }

    # ── Submitters ───────────────────────────────────────────────────────────

    def _submit_text2video(self, scene_id: str, prompt: str,
                           duration: int, aspect_ratio: str,
                           model: str = "", mode: str = "") -> Optional[str]:
        payload = {
            "model_name":   model or HEIJMANS_CONFIG["kling"]["model"],
            "prompt":       prompt,
            "duration":     duration,
            "aspect_ratio": aspect_ratio,
            "cfg_scale":    HEIJMANS_CONFIG["kling"]["cfg_scale"],
            "mode":         mode or HEIJMANS_CONFIG["kling"]["mode"],
            "negative_prompt": (
                "blur, distortion, watermark, low quality, text, letters, "
                "artificial, CGI, cartoon, anime"
            ),
        }
        try:
            r = requests.post(
                f"{self.base_url}/v1/videos/text2video",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            data = r.json()
            task_id = (data.get("data") or {}).get("task_id") or data.get("task_id")
            if task_id:
                print(f"   ✅ text2video ingediend: {scene_id} → {task_id}")
                return task_id
            print(f"   ❌ text2video fout ({scene_id}): {data}")
            return None
        except Exception as e:
            print(f"   ❌ text2video exception ({scene_id}): {e}")
            return None

    def _submit_image2video(self, scene_id: str, image_path: Path,
                             prompt: str, duration: int,
                             aspect_ratio: str) -> Optional[str]:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "model_name":   HEIJMANS_CONFIG["kling"]["model"],
            "image":        img_b64,
            "prompt":       prompt,
            "duration":     duration,
            "aspect_ratio": aspect_ratio,
            "cfg_scale":    HEIJMANS_CONFIG["kling"]["cfg_scale"],
            "mode":         HEIJMANS_CONFIG["kling"]["mode"],
        }
        try:
            r = requests.post(
                f"{self.base_url}/v1/videos/image2video",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            data = r.json()
            task_id = (data.get("data") or {}).get("task_id") or data.get("task_id")
            if task_id:
                print(f"   ✅ image2video ingediend: {scene_id} → {task_id}")
                return task_id
            print(f"   ❌ image2video fout ({scene_id}): {data}")
            return None
        except Exception as e:
            print(f"   ❌ image2video exception ({scene_id}): {e}")
            return None

    # ── Polling ──────────────────────────────────────────────────────────────

    def _poll(self, task_id: str, video_type: str = "text2video",
              max_wait: int = 900, interval: int = 15) -> Optional[str]:
        endpoint = f"{self.base_url}/v1/videos/{video_type}/{task_id}"
        start = time.time()
        while time.time() - start < max_wait:
            try:
                r = requests.get(endpoint, headers=self._headers(), timeout=15)
                data = r.json().get("data", {})
                status = data.get("task_status", "")
                print(f"      ⏳ {task_id[:12]}… status: {status}")

                if status == "succeed":
                    videos = data.get("task_result", {}).get("videos", [])
                    if videos:
                        return videos[0].get("url")
                elif status in ("failed", "error"):
                    return None
            except Exception as e:
                print(f"      ⚠️  poll fout: {e}")
            time.sleep(interval)

        print(f"      ❌ Timeout na {max_wait}s")
        return None

    # ── Public API ───────────────────────────────────────────────────────────

    def create_video(self, scene_id: str, prompt: str,
                     duration: int = 5, aspect_ratio: str = "9:16",
                     image_path: Optional[Path] = None, **kwargs) -> Optional[str]:
        """
        Dien één video taak in.
        Geeft task_id terug of None bij fout.
        """
        if image_path and Path(image_path).exists():
            return self._submit_image2video(
                scene_id, Path(image_path), prompt, duration, aspect_ratio)
        return self._submit_text2video(
            scene_id, prompt, duration, aspect_ratio,
            model=kwargs.get("model", ""),
            mode=kwargs.get("mode", ""),
        )

    def wait_for_completion(self, task_id: str,
                            video_type: str = "text2video",
                            max_wait: int = 900) -> Optional[str]:
        """Poll tot video klaar. Geeft URL terug of None."""
        return self._poll(task_id, video_type, max_wait)

    def generate_batch(self, scenes: dict,
                       aspect_ratio: str = "9:16",
                       output_dir: Optional[Path] = None) -> dict:
        """
        Genereer meerdere video's in batch.

        scenes formaat:
          {
            "scene_id": {
              "type":     "text2video" | "image2video",
              "prompt":   "...",
              "duration": 5,
              "image":    Path (alleen bij image2video)
            }
          }

        Geeft terug:
          {
            "scene_id": {
              "task_id":   "...",
              "video_url": "...",
              "status":    "completed|failed|timeout"
            }
          }
        """
        results = {}
        task_ids = {}

        # 1. Submit alle jobs
        print(f"\n1️⃣  Jobs indienen bij Kling ({len(scenes)} scenes)...")
        for scene_id, cfg in scenes.items():
            task_id = self.create_video(
                scene_id     = scene_id,
                prompt       = cfg["prompt"],
                duration     = cfg.get("duration", 5),
                aspect_ratio = cfg.get("aspect_ratio", aspect_ratio),
                image_path   = cfg.get("image"),
                model        = cfg.get("model", ""),
                mode         = cfg.get("mode", ""),
            )
            if task_id:
                task_ids[scene_id] = (task_id, cfg.get("type", "text2video"))
                results[scene_id]  = {"task_id": task_id, "status": "queued"}
                self._log(scene_id, task_id, cfg["prompt"])
            else:
                results[scene_id] = {"status": "submission_failed"}
            time.sleep(2)

        # 2. Poll en download
        print(f"\n2️⃣  Wachten op resultaten...")
        for scene_id, (task_id, vtype) in task_ids.items():
            video_url = self._poll(task_id, vtype)
            if video_url:
                results[scene_id]["video_url"] = video_url
                results[scene_id]["status"]    = "completed"
                self._log_done(task_id, video_url)

                # Optioneel downloaden
                if output_dir:
                    out = Path(output_dir) / f"{scene_id}.mp4"
                    self._download(video_url, out)
                    results[scene_id]["local_path"] = str(out)
            else:
                results[scene_id]["status"] = "failed_or_timeout"

        return results

    # ── Download ─────────────────────────────────────────────────────────────

    def _download(self, url: str, path: Path) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(url, timeout=120, stream=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            size_mb = path.stat().st_size / 1_000_000
            print(f"      💾 {path.name} ({size_mb:.1f} MB)")
            return True
        except Exception as e:
            print(f"      ❌ Download fout: {e}")
            return False

    # ── Logging ──────────────────────────────────────────────────────────────

    def _log(self, scene_id: str, task_id: str, prompt: str):
        self.log.append({
            "scene_id":     scene_id,
            "task_id":      task_id,
            "prompt":       prompt[:120] + "…",
            "submitted_at": datetime.now().isoformat(),
            "status":       "queued",
        })

    def _log_done(self, task_id: str, video_url: str):
        for entry in self.log:
            if entry["task_id"] == task_id:
                entry["status"]       = "completed"
                entry["video_url"]    = video_url
                entry["completed_at"] = datetime.now().isoformat()

    def save_log(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.log, indent=2, ensure_ascii=False))
        print(f"📋 Log opgeslagen: {path}")

    def test_auth(self) -> bool:
        """Test JWT auth. Geeft True terug als API bereikbaar is."""
        print("🔑 Kling JWT auth test...")
        token = self._jwt_token()
        print(f"   Token: {token[:40]}…")
        try:
            r = requests.get(
                f"{self.base_url}/v1/videos/text2video",
                headers=self._headers(), timeout=10,
            )
            print(f"   Status: {r.status_code}")
            ok = r.status_code in (200, 400)  # 400 = no params maar auth OK
            print(f"   Auth: {'✅ OK' if ok else '❌ Mislukt'}")
            return ok
        except Exception as e:
            print(f"   ❌ {e}")
            return False


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kling Video Generator — JWT auth")
    parser.add_argument("--test-auth",         action="store_true", help="Test JWT auth")
    parser.add_argument("--heijmans",          action="store_true", help="Run Heijmans B1-B4 batch")
    parser.add_argument("--werkvoorbereider",  action="store_true", help="Run Werkvoorbereider BTS (variant A)")
    parser.add_argument("--werkvoorbereider-a", action="store_true", help="Run Werkvoorbereider BTS variant A (v2-6 std)")
    parser.add_argument("--werkvoorbereider-b", action="store_true", help="Run Werkvoorbereider BTS variant B (v1.5 pro)")
    parser.add_argument("--dry-run",           action="store_true", help="Toon scenes, geen API calls")
    parser.add_argument("--output-dir",        type=Path, default=Path("/tmp/recruitin-local/heijmans"))
    args = parser.parse_args()

    gen = KlingVideoGenerator()

    if args.test_auth:
        gen.test_auth()
        sys.exit(0)

    # Selecteer scenes op basis van flag
    scenes = HEIJMANS_SCENES
    label  = "Heijmans B1-B4"
    if getattr(args, "werkvoorbereider_b", False):
        scenes = WERKVOORBEREIDER_B
        label  = "Werkvoorbereider BTS — Variant B (v1.5 pro)"
    elif getattr(args, "werkvoorbereider_a", False) or args.werkvoorbereider:
        scenes = WERKVOORBEREIDER_A
        label  = "Werkvoorbereider BTS — Variant A (v2-6 std)"

    if args.dry_run:
        print(f"🎬 DRY RUN — {label} scenes:")
        for sid, cfg in scenes.items():
            print(f"\n  [{sid}]")
            print(f"  Type:     {cfg['type']}")
            print(f"  Duration: {cfg['duration']}s")
            print(f"  Prompt:   {cfg['prompt'][:200]}…")
        sys.exit(0)

    if args.heijmans or args.werkvoorbereider or getattr(args, "werkvoorbereider_a", False) or getattr(args, "werkvoorbereider_b", False):
        print(f"🎬 {label} starten...")
        results = gen.generate_batch(
            scenes     = scenes,
            output_dir = args.output_dir,
        )
        gen.save_log(args.output_dir / "video_log.json")

        print("\n📊 RESULTAAT:")
        for scene_id, r in results.items():
            status = r.get("status", "?")
            url    = r.get("video_url", "")
            local  = r.get("local_path", "")
            print(f"  {scene_id}: {status}")
            if url:   print(f"    URL:   {url[:80]}")
            if local: print(f"    File:  {local}")
