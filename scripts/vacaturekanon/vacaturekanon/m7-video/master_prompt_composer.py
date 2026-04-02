#!/usr/bin/env python3
"""
master_prompt_composer.py — Vacaturekanon Master Prompt v2.0
Compositeert ultra-realistische image + motion prompts per sector, rol en scene.

Gebaseerd op Heijmans BTS deep dive analyse — 8 kwaliteitsfactoren verwerkt.
Output prompts zijn geoptimaliseerd voor Nano Banana Pro (Antigravity).

Usage:
    python3 master_prompt_composer.py --sector automation --rol "PLC Engineer" --scene conversion
    python3 master_prompt_composer.py --sector constructie --rol "Uitvoerder" --all-scenes
    python3 master_prompt_composer.py --list-sectors
"""

import argparse
import json
import sys
from pathlib import Path

# ── Character DNA Library ─────────────────────────────────────────────────

CHARACTER_DNA = {
    "automation": {
        "description": "PLC / Automation / Electrical engineer",
        "dna": (
            "Mid-to-late 30s Dutch male electrical automation engineer. "
            "Short dark brown hair, clean-cut but not styled, slightly windswept near the ears. "
            "3-day stubble beard, slim rectangular glasses, focused-calm expression — "
            "the look of someone who makes complex systems work, not a manager who watches. "
            "Navy blue company polo shirt, sleeves rolled to just below the elbow. "
            "Dark navy work trousers with a slightly technical cut. "
            "Brown leather lace-up work shoes, practical not fashionable. "
            "Hands: clean, precise engineer's hands — one holding a multimeter probe "
            "or resting on a laptop keyboard showing Siemens TIA Portal."
        ),
        "secondary": (
            "A younger male colleague (late 20s, similar attire, no glasses) "
            "visible in soft background bokeh, looking at a schematic on a tablet"
        ),
    },
    "constructie": {
        "description": "Bouwplaats uitvoerder / foreman (bewezen Heijmans DNA)",
        "dna": (
            "Early-to-mid 40s Dutch male construction foreman. "
            "Short dark-brown hair, salt-and-pepper at the temples, slightly windswept. "
            "3-day stubble beard, strong pronounced jaw, sun-weathered skin with fine lines "
            "at the eyes — not old, but experienced and credible. "
            "Bright ORANGE high-vis softshell jacket with grey reflective chest stripes, "
            "small company logo embroidered on left chest. "
            "YELLOW hard hat pushed slightly back — not perfectly centered, worn-in. "
            "Dark navy work trousers, muddy steel-toed work boots. "
            "Hands: calloused and strong, working-man's hands with slight grime under the nails."
        ),
        "secondary": (
            "A crew member in orange vest visible at the edge of frame, "
            "looking at blueprints or managing equipment in the background"
        ),
    },
    "oil_gas": {
        "description": "Offshore / Refinery operations engineer",
        "dna": (
            "Late 40s Dutch male offshore operations supervisor. "
            "Short grey-brown hair cropped close, thick 5-day beard with visible grey. "
            "Salt spray on weathered deeply tanned skin, deep-set blue eyes with permanent "
            "squint lines from years of offshore wind — a face that tells a story. "
            "ORANGE flame-resistant FR coverall (Nomex-type, faded from use), "
            "white hard hat with company logo sticker, safety glasses pushed up on forehead. "
            "Heavy-duty work gloves tucked into a chest pocket. "
            "Expression: pragmatic, unflappable, seen-it-all calm."
        ),
        "secondary": (
            "Another engineer with a clipboard visible in background "
            "next to large industrial piping infrastructure"
        ),
    },
    "productie": {
        "description": "Productie manager / factory operations",
        "dna": (
            "Early 40s Dutch male production manager. "
            "Short neat dark hair, clean-shaved with a day's shadow at most. "
            "Confident open expression — results-oriented but collaborative. "
            "Dark company polo or button-down work shirt with logo, "
            "dark chinos or work trousers, safety shoes (brown leather). "
            "Often holding a tablet or clipboard showing production data. "
            "Expression: in control, decisive, problem-solving focus."
        ),
        "secondary": (
            "Production line workers visible in background operating CNC machinery "
            "or quality-checking components"
        ),
    },
    "renewable": {
        "description": "Wind energy / solar project engineer",
        "dna": (
            "Early 40s Dutch male renewable energy project engineer. "
            "Short neat dark hair, clean shave or light stubble, open forward-looking expression. "
            "Bright ORANGE high-vis zip jacket over a company polo, "
            "YELLOW hard hat (clean, newer than construction sector), "
            "harness attachment points visible at shoulders when in field. "
            "Expression: energetic, genuinely proud of the work's impact, "
            "not a corporate poster — a real engineer."
        ),
        "secondary": (
            "A colleague with a laptop and drone controller visible in background "
            "at base of a wind turbine"
        ),
    },
}

# ── Environment Library ────────────────────────────────────────────────────

ENVIRONMENTS = {
    "automation_workshop": {
        "description": "Electrical assembly hall — indoor",
        "env": (
            "Modern Dutch industrial electrical assembly hall. "
            "Polished light grey epoxy floor (RAL 7035 tone), "
            "white-painted concrete block walls, "
            "high ceiling (6 meter) with industrial LED strip lighting at 5000K — "
            "bright, clinical, professional. "
            "Steel workbenches with anti-static mats. "
            "Rittal VX25 switchgear cabinets (light grey RAL 7035) in a row. "
            "Phoenix Contact orange terminal blocks, white cable management ducts overhead. "
            "Neat red and blue cable bundles visible inside open cabinet doors. "
            "The space feels organised, spacious, serious."
        ),
    },
    "automation_office": {
        "description": "Engineering office with schematics",
        "env": (
            "Modern open-plan Dutch engineering office. "
            "Large windows, grey carpet, ergonomic sit-stand desks. "
            "Second monitor showing CAD schematic or P&ID diagram. "
            "Physical A0 electrical drawings pinned to a board in background. "
            "Colleagues at desks softly blurred (2-3 people visible). "
            "Coffee mug, Staedtler pens, printed schematics on the desk — "
            "not empty and sterile, used and real."
        ),
    },
    "construction_highway": {
        "description": "Dutch A-road construction site — outdoor",
        "env": (
            "Flat Dutch highway construction site (A-road type — A12 or A15 style). "
            "Concrete sound barriers and orange jersey barriers lining the work zone. "
            "That specific Netherlands polder landscape — wide, flat, grey-white "
            "overcast Dutch sky that filters light evenly without harsh shadows. "
            "Distant wind turbines barely visible through the horizon haze. "
            "Fresh tarmac, orange road barriers, yellow excavators in the distance."
        ),
    },
    "construction_night": {
        "description": "Highway construction at night — dramatic",
        "env": (
            "Dutch highway construction site at night (23:00). "
            "Powerful 6000K LED construction flood lights create dramatic volumetric "
            "light beams cutting through steam and diesel exhaust. "
            "Wet fresh asphalt reflects all the construction lights. "
            "Orange warning lights pulse on machinery. "
            "Dutch night sky: sodium lamp orange glow on the horizon from distant city, "
            "dark blue-black above, scattered cumulus clouds faintly lit."
        ),
    },
    "oil_gas_refinery": {
        "description": "Oil refinery or offshore platform",
        "env": (
            "Large Dutch industrial petrochemical facility or offshore platform. "
            "Massive stainless steel pipe networks, pressure vessels, flare stacks. "
            "Industrial scaffolding, valve manifolds, cable trays everywhere. "
            "Either golden hour or overcast Dutch sky. "
            "Wet metal grating underfoot, safety signage in Dutch and English."
        ),
    },
    "renewable_field": {
        "description": "Wind turbine field or solar farm",
        "env": (
            "Dutch renewable energy site — wind turbine base or large solar array. "
            "Flat polder landscape, wide Dutch horizon, "
            "that characteristic grey-white overcast sky. "
            "White wind turbine towers rising 120+ meters. "
            "Green grass between turbine bases, gravel access roads. "
            "Clean, modern, scale is impressive."
        ),
    },
}

# ── Lighting Library ──────────────────────────────────────────────────────

LIGHTING = {
    "golden_hour": (
        "Warm golden side-light from setting sun (Dutch autumn afternoon, ~17:00), "
        "creating a long soft shadow to the right. "
        "Sky is warm orange-gold at the horizon. "
        "This light makes skin tones warm and human — not clinical."
    ),
    "overcast_dutch": (
        "Flat cool overcast Dutch sky provides perfectly diffused shadowless light. "
        "No harsh highlights, no deep shadows — documentary-honest. "
        "Slightly cool colour temperature (6500K) typical Netherlands daytime."
    ),
    "factory_led_with_window": (
        "Cool 5000K LED overhead strip fills from above creating crisp professional light. "
        "End-of-day warm golden light streams through tall factory windows from the right, "
        "creating a warm rim light on the subject's profile against the cool LED fill. "
        "The combination makes the scene feel alive and warm, not sterile."
    ),
    "night_floodlight": (
        "Powerful construction flood lights create dramatic volumetric light beams. "
        "Subject is sharply lit from front-left with deep dramatic shadow on right side. "
        "Wet surfaces reflect all the light. Atmosphere: epic, purposeful, cinematic."
    ),
    "end_of_day_factory": (
        "Late afternoon warm golden light through industrial skylights creates "
        "god-ray beams cutting through dust particles in the air. "
        "This is the moment of day when a factory feels most human and warm."
    ),
}

# ── Scene Templates ────────────────────────────────────────────────────────

SCENE_CONFIGS = {
    "awareness": {
        "description": "Eerste indruk — personage in herkenbare werkomgeving",
        "camera": "85mm portrait lens, f/2.0, very slight handheld micro-shake",
        "action": (
            "stands confidently in his workspace, slightly turned toward camera, "
            "weight on one foot — not posing, caught in a natural moment between tasks. "
            "Micro-expression: quiet concentration, on top of it, where he belongs."
        ),
        "motion_prompt": (
            "The engineer shifts his weight slightly and glances up from what he was doing, "
            "makes brief natural eye contact with the camera — not a pose, a candid moment. "
            "A colleague passes behind him. Equipment hums. "
            "Very subtle camera drift, handheld documentary feel, natural pace. "
            "End on him returning focus to his work with a slight nod."
        ),
    },
    "consideration": {
        "description": "Teamwork en expertise — actief bezig met collega",
        "camera": "35mm lens, f/2.8, slightly wider, two-person frame",
        "action": (
            "leans over a steel workbench together with a colleague, "
            "both studying a schematic or open laptop screen. "
            "His right hand points to a specific detail on the screen or drawing. "
            "Micro-expression: collaborative focus, explaining something with conviction. "
            "The colleague listens and responds — genuine dialogue, not staged."
        ),
        "motion_prompt": (
            "He and his colleague discuss something at the workbench. "
            "His hand moves across the schematic pointing out details, "
            "the colleague nods and asks a question. "
            "Natural conversation body language — no stiffness. "
            "Camera very slow push-in, documentary feel. "
            "Other colleagues visible in soft background, life happening around them."
        ),
    },
    "conversion": {
        "description": "Actief testen / commissioning — het echte vakwerk",
        "camera": "85mm lens, f/2.0, slight crouch angle looking slightly up",
        "action": (
            "crouches or leans forward in an active testing pose in front of "
            "an OPEN switchgear cabinet or control panel. "
            "One hand gently rests on or touches a component, "
            "the other holds a multimeter probe or laptop. "
            "Micro-expression: the concentrated furrow of the brow of someone "
            "diagnosing a system — this is the moment of truth."
        ),
        "motion_prompt": (
            "He leans in close to the open cabinet, adjusting a connection or "
            "checking a reading on his multimeter. "
            "Small precise hand movements, leaning back slightly to check the laptop screen, "
            "then leaning in again. "
            "The HMI display behind him flickers and changes to green status. "
            "A slight satisfied exhale — the system responds. "
            "Camera very slow pull-back to reveal the full workspace. "
            "Documentary, intimate, this is what it actually looks like."
        ),
    },
    "char_front": {
        "description": "Karakterportret — front facing, professioneel",
        "camera": "85mm portrait lens, f/1.8, perfectly sharp subject, deep bokeh background",
        "action": (
            "faces camera directly in a relaxed but confident three-quarter stance. "
            "Arms hang naturally at sides or one hand rests in pocket. "
            "Micro-expression: approachable warmth with quiet professional confidence. "
            "This is NOT a LinkedIn headshot. This is a quiet moment of a real person."
        ),
        "motion_prompt": (
            "He stands calm, a natural breath visible in the rise of his chest. "
            "He glances slightly to the left then back — "
            "a candid moment, not a pose held for a camera. "
            "Very subtle environmental movement: fabric, background activity. "
            "Camera completely static, anchored to the moment."
        ),
    },
}

# ── Negative Prompt ────────────────────────────────────────────────────────

NEGATIVE_PROMPT = (
    "text, letters, words, numbers, watermark, logo, signature, "
    "extra arms, extra hands, extra fingers, six fingers, fused limbs, "
    "double limbs, merged body parts, wrong anatomy, deformed hands, "
    "extra people merged into subject, floating limbs, "
    "plastic skin, waxy appearance, stock photo smile, "
    "arms-crossed corporate portrait, posed looking straight at camera smiling unnaturally, "
    "cartoon, illustration, painting, render, CGI look, "
    "blurry, low quality, low resolution, "
    "studio backdrop, seamless paper background, ring light catch in eyes, "
    "boom microphone, visible camera crew equipment, "
    "neon colors, oversaturated, HDR overprocessed, "
    "sci-fi, futuristic, holographic displays, unrealistic technology"
)

# ─────────────────────────────────────────────────────────────────────────


def compose_prompt(
    sector: str,
    scene: str,
    rol: str = "",
    extra_context: str = "",
    lighting_key: str = None,
    environment_key: str = None,
) -> dict:
    """
    Compositeert een volledig image prompt + motion prompt voor de gegeven combinatie.
    Returns: {"prompt": str, "motion_prompt": str, "negative_prompt": str, "chars": int}
    """
    char_data = CHARACTER_DNA.get(sector)
    if not char_data:
        available = list(CHARACTER_DNA.keys())
        raise ValueError(f"Onbekende sector '{sector}'. Beschikbaar: {available}")

    scene_cfg = SCENE_CONFIGS.get(scene)
    if not scene_cfg:
        available = list(SCENE_CONFIGS.keys())
        raise ValueError(f"Onbekende scene '{scene}'. Beschikbaar: {available}")

    # Kies standaard environment per sector+scene combinatie
    if not environment_key:
        environment_key = _default_environment(sector, scene)
    env_data = ENVIRONMENTS.get(environment_key, {})

    # Kies standaard licht per sector+scene
    if not lighting_key:
        lighting_key = _default_lighting(sector, scene)
    light = LIGHTING.get(lighting_key, "")

    # Rol label
    rol_label = rol if rol else char_data["description"]

    # ── Bouw 5-laags prompt ───────────────────────────────────────────────
    parts = [
        # LAYER 1: Camera
        f"{scene_cfg['camera']}.",

        # LAYER 2: Character + Actie
        f"{char_data['dna']}.",
        f"He {scene_cfg['action']}",

        # LAYER 3: Secundair personage
        f"{char_data['secondary']}.",

        # LAYER 4: Omgeving + Licht
        env_data.get("env", ""),
        light,

        # LAYER 5: Authenticiteit
        "Dutch documentary workplace photography — "
        "candid, unposed, this could be a frame from a NOS reportage "
        "about Dutch industrial excellence. "
        "Shot on Sony A7IV with Zeiss lens. Photorealistic 8K.",
    ]

    if extra_context:
        parts.insert(4, extra_context)

    prompt = " ".join(p for p in parts if p).strip()

    # Truncate to 1500 chars (Leonardo / Nano Banana limit)
    if len(prompt) > 1500:
        prompt = prompt[:1497] + "..."

    return {
        "prompt": prompt,
        "motion_prompt": scene_cfg["motion_prompt"],
        "negative_prompt": NEGATIVE_PROMPT,
        "chars": len(prompt),
        "sector": sector,
        "scene": scene,
        "rol": rol_label,
        "environment": environment_key,
        "lighting": lighting_key,
    }


def _default_environment(sector: str, scene: str) -> str:
    """Kies standaard environment op basis van sector en scene."""
    mapping = {
        ("automation", "char_front"):    "automation_workshop",
        ("automation", "awareness"):     "automation_workshop",
        ("automation", "consideration"): "automation_workshop",
        ("automation", "conversion"):    "automation_workshop",
        ("constructie", "char_front"):   "construction_highway",
        ("constructie", "awareness"):    "construction_highway",
        ("constructie", "consideration"): "construction_highway",
        ("constructie", "conversion"):   "construction_night",
        ("oil_gas", "char_front"):       "oil_gas_refinery",
        ("oil_gas", "awareness"):        "oil_gas_refinery",
        ("oil_gas", "consideration"):    "oil_gas_refinery",
        ("oil_gas", "conversion"):       "oil_gas_refinery",
        ("productie", "char_front"):     "automation_workshop",
        ("productie", "awareness"):      "automation_workshop",
        ("productie", "consideration"):  "automation_workshop",
        ("productie", "conversion"):     "automation_workshop",
        ("renewable", "char_front"):     "renewable_field",
        ("renewable", "awareness"):      "renewable_field",
        ("renewable", "consideration"):  "automation_office",
        ("renewable", "conversion"):     "renewable_field",
    }
    return mapping.get((sector, scene), "automation_workshop")


def _default_lighting(sector: str, scene: str) -> str:
    """Kies standaard licht op basis van sector en scene."""
    if sector == "constructie" and scene == "conversion":
        return "night_floodlight"
    if sector == "constructie":
        return "golden_hour"
    if scene in ("awareness", "char_front"):
        return "factory_led_with_window"
    if scene == "conversion":
        return "factory_led_with_window"
    return "overcast_dutch"


def print_prompt(result: dict, verbose: bool = False):
    """Print het gegenereerde prompt naar stdout."""
    print(f"\n{'='*70}")
    print(f"  Sector  : {result['sector']}")
    print(f"  Scene   : {result['scene']}")
    print(f"  Rol     : {result['rol']}")
    print(f"  Chars   : {result['chars']}/1500")
    print(f"{'='*70}")
    print(f"\n📸 IMAGE PROMPT:\n{result['prompt']}")
    if verbose:
        print(f"\n🎬 MOTION PROMPT:\n{result['motion_prompt']}")
        print(f"\n🚫 NEGATIVE PROMPT:\n{result['negative_prompt']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Vacaturekanon Master Prompt Composer v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python3 master_prompt_composer.py --sector automation --scene awareness
  python3 master_prompt_composer.py --sector constructie --rol "Uitvoerder" --all-scenes --verbose
  python3 master_prompt_composer.py --list-sectors
  python3 master_prompt_composer.py --sector automation --scene conversion --json
        """
    )
    parser.add_argument("--sector",     help="Sector (automation/constructie/oil_gas/productie/renewable)")
    parser.add_argument("--scene",      help="Scene (awareness/consideration/conversion/char_front)")
    parser.add_argument("--rol",        default="", help="Specifieke functietitel (optioneel)")
    parser.add_argument("--all-scenes", action="store_true", help="Genereer alle 4 scenes")
    parser.add_argument("--verbose",    action="store_true", help="Toon ook motion + negative prompt")
    parser.add_argument("--json",       action="store_true", help="Output als JSON")
    parser.add_argument("--list-sectors", action="store_true", help="Toon beschikbare sectoren")
    args = parser.parse_args()

    if args.list_sectors:
        print("\nBeschikbare sectoren:")
        for k, v in CHARACTER_DNA.items():
            print(f"  {k:<12} → {v['description']}")
        print("\nBeschikbare scenes:")
        for k, v in SCENE_CONFIGS.items():
            print(f"  {k:<12} → {v['description']}")
        return

    if not args.sector:
        parser.print_help()
        sys.exit(1)

    scenes = list(SCENE_CONFIGS.keys()) if args.all_scenes else [args.scene or "awareness"]

    results = []
    for scene in scenes:
        try:
            result = compose_prompt(args.sector, scene, rol=args.rol)
            results.append(result)
            if not args.json:
                print_prompt(result, verbose=args.verbose)
        except ValueError as e:
            print(f"❌ Fout: {e}", file=sys.stderr)
            sys.exit(1)

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
