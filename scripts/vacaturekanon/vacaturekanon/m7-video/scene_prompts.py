"""
scene_prompts.py — Vacaturekanon cinematische prompts voor Leonardo + Kling
===========================================================================
Per sector × shot type (character / scene image prompt) +
Per sector × scene (Kling motion prompt)

Gebruik:
    from scene_prompts import get_image_prompt, get_motion_prompt, CHARACTER_DNA
"""

# ── Character DNA (per sector) ────────────────────────────────────────────────
# Gebaseerd op Recruitin B.V. standaard: begin-40s West-Europese man

CHARACTER_DNA = {
    "oil-gas": (
        "Early 40s Western European male petroleum engineer, short dark brown hair "
        "neatly combed, light stubble beard, strong jawline, confident approachable expression, "
        "wearing dark navy blue technical work jacket with subtle company logo on chest, "
        "dark work trousers, oil refinery or petrochemical plant environment"
    ),
    "constructie": (
        "Early 40s Western European male construction foreman, short dark brown hair "
        "neatly combed, light stubble beard, strong jawline, confident approachable expression, "
        "wearing bright ORANGE high-visibility full zip jacket with grey reflective stripes, "
        "YELLOW safety hard hat, dark work trousers, "
        "Dutch road or building construction site environment"
    ),
    "automation": (
        "Mid-30s to mid-40s Western European male PLC engineer, short dark brown hair "
        "slightly dishevelled from a long workday, light stubble beard 2-3 days, "
        "focused intelligent expression, slight fatigue around the eyes, "
        "wearing a dark navy blue company polo shirt or button-up technical shirt, "
        "dark work trousers, safety glasses pushed up on forehead, "
        "clean modern Dutch industrial electrical assembly hall: "
        "white or light gray painted concrete walls, epoxy-coated concrete floor, "
        "LED strip lighting on high industrial ceiling, steel workbenches, "
        "Rittal VX25 cabinets in RAL 7035 light gray, Phoenix Contact orange terminals, "
        "cable trays overhead, organized and professional — NOT rustic, NOT wood, NOT dark"
    ),
    "productie": (
        "Early 40s Western European male production supervisor, short dark brown hair "
        "neatly combed, light stubble beard, strong jawline, confident approachable expression, "
        "wearing dark blue or navy work jacket with company logo, safety glasses on forehead, "
        "dark work trousers, modern manufacturing or production facility environment"
    ),
    "renewable": (
        "Early 40s Western European male renewable energy engineer, short dark brown hair "
        "neatly combed, light stubble beard, strong jawline, confident approachable expression, "
        "wearing bright ORANGE high-visibility full zip jacket, YELLOW safety hard hat, "
        "dark work trousers, wind turbines or solar farm environment"
    ),
    "sales-b2b": (
        "HR manager (40s, professional attire), frustrated yet professional expression"
    ),
}

NEGATIVE_PROMPT = (
    "text, letters, words, numbers, watermark, logo, AI artifacts, distortion, "
    "extra fingers, extra arms, extra limbs, double arms, fused arms, merged limbs, "
    "wrong anatomy, deformed hands, mutated body, anatomical errors, "
    "plastic appearance, stock photo look, "
    "cartoon, illustration, painting, blurry, low quality, neon colors, "
    "sci-fi, futuristic, glowing holographic, robots, neon LED strips, "
    "posed symmetric, arms crossed looking at camera, perfect hair, clean studio, "
    "stock smile, centered portrait, boom microphone, surgical clean room"
)

# ── Image prompts voor Leonardo (character reference + scene stills) ───────────
# Elke scene heeft een 'image' prompt voor Leonardo (de still) +
# een 'motion' prompt voor Kling (de animatie van die still)

IMAGE_PROMPTS = {
    "oil-gas": {
        "char_front": (
            "{char}. Standing facing camera directly, frontal portrait shot, "
            "oil refinery background with pipes and towers blurred, "
            "dusk golden hour light, 85mm portrait lens, shallow depth of field, "
            "editorial documentary photography, hyperrealistic 8K, photorealistic"
        ),
        "awareness": (
            "Cinematic aerial view over a Dutch oil refinery at golden hour. "
            "Massive industrial complex with pipes, distillation towers and storage tanks. "
            "One control room visible with empty desk chair and glowing screens. "
            "Atmosphere of urgency, industrial scale. No people. "
            "85mm lens equivalent, shallow depth, cinematic color grade warm amber. "
            "9:16 portrait format, hyperrealistic 8K, photorealistic."
        ),
        "consideration": (
            "{char}. Standing confidently at laptop or tablet in petrochemical plant office, "
            "refinery complex visible through large windows behind him. "
            "Engaged expression, forward-leaning posture showing energy and action. "
            "Natural office lighting warm, 85mm portrait lens soft bokeh. "
            "9:16 portrait format, hyperrealistic 8K, photorealistic, documentary style."
        ),
        "conversion": (
            "{char}. Shaking hands with a younger engineer colleague in front of refinery equipment. "
            "Both smiling genuinely, natural body language. Orange safety elements visible. "
            "Golden hour light filtering through industrial windows. "
            "Camera slightly low angle, warm cinematic grade. "
            "9:16 portrait format, hyperrealistic 8K, photorealistic."
        ),
    },
    "constructie": {
        "char_front": (
            "{char}. Standing facing camera directly, frontal portrait shot, "
            "road construction site background with excavator blurred, "
            "overcast Dutch daylight, 85mm portrait lens, shallow depth of field, "
            "editorial documentary photography, hyperrealistic 8K, photorealistic"
        ),
        "awareness": (
            "Dutch construction site project office interior. Blueprints spread on a table, "
            "phone ringing unanswered, sticky note on whiteboard reading 'VACATURE OPEN'. "
            "Project planning screen showing delays in red. Long shadows, late afternoon. "
            "Urgency and understaffing atmosphere. No people. "
            "9:16 portrait format, cinematic color grade, hyperrealistic 8K."
        ),
        "consideration": (
            "{char}. Standing at a large site briefing table with blueprints, "
            "Dutch construction site visible through windows behind him. "
            "Gesturing with confidence, engaged and authoritative. "
            "Hard hat on table beside him. Warm overcast daylight. "
            "85mm portrait lens, shallow depth of field. "
            "9:16 portrait format, hyperrealistic 8K, documentary photography."
        ),
        "conversion": (
            "{char}. Standing on completed Dutch infrastructure project — bridge or road — "
            "pointing into the distance with satisfied proud expression. "
            "Small team of engineers behind him reviewing plans. "
            "Golden hour lighting, sense of completion and pride. "
            "Camera slowly low angle. Orange safety vest elements visible. "
            "9:16 portrait format, hyperrealistic 8K, cinematic."
        ),
    },
    "automation": {
        "char_front": (
            "{char}. Standing 3/4 angle looking at open Rittal VX25 cabinet (RAL 7035 light gray) "
            "on steel workbench, not facing camera. "
            "Phoenix Contact orange terminal blocks inside cabinet, neat cable bundles. "
            "Colleague blurred in background at matching workbench. "
            "Clean modern industrial assembly hall: white concrete walls, epoxy floor, LED ceiling, cable trays. "
            "85mm lens, f/1.8, shallow DOF. Hyperrealistic 8K. NOT wood, NOT rustic."
        ),
        "awareness": (
            "Modern clean Dutch electrical assembly hall, end-of-day golden light through high factory windows. "
            "A Rittal VX25 cabinet (light gray) stands open on a steel workbench — half-wired interior: "
            "Phoenix Contact orange terminal blocks, red and blue cables half-bundled, cable duct lid off. "
            "A laptop open beside it shows Siemens TIA Portal — unattended, screen still on. "
            "Empty metal stool pulled back. A safety thermos and a pen on the bench. "
            "Walls: white painted concrete. Floor: light gray epoxy. Ceiling: LED strip lighting. "
            "Spacious, organized, professional — clearly a real engineering company. "
            "9:16 portrait format, documentary B-roll, hyperrealistic 8K photorealistic. "
            "Warm natural light from windows mixing with neutral LED — inviting, NOT sterile, NOT sci-fi."
        ),
        "consideration": (
            "{char}. Leaning over a workbench studying Siemens TIA Portal on a laptop, "
            "pointing at a specific ladder logic rung with a pen. "
            "A younger colleague stands beside him (slightly blurred), looking at the same screen — "
            "a natural moment of knowledge-sharing, shoulder-to-shoulder. "
            "The main engineer explains something; his colleague nods. Both focused, relaxed. "
            "Siemens or Bachmann PLC module connected to the laptop by USB cable on the bench. "
            "Phoenix Contact terminals in labelled bins, electrical schematic spread open nearby. "
            "Warm tungsten overhead light, soft shadows — inviting, collegial atmosphere. "
            "85mm lens, f/2, slight motion blur on pointing hand. "
            "9:16 portrait, hyperrealistic 8K, documentary style. Warm and real."
        ),
        "conversion": (
            "Open Rittal VX25 switchgear cabinet (light gray) interior close-up — "
            "immaculate wiring: red, blue, black cable bundles through white cable ducts, "
            "Siemens S7-1200 PLC on DIN rail with green status LEDs glowing, "
            "Phoenix Contact orange terminals neatly labelled, 24V power supply green indicator on, "
            "Ethernet cables plugged in. "
            "{char} partially in frame right side, holding laptop (TIA Portal visible), "
            "presses a button on PLC — HMI panel transitions to green RUNNING. "
            "Quiet half-smile. First live moment. Cabinet-level camera angle. "
            "9:16, hyperrealistic 8K. Real craftsmanship, NOT sterile."
        ),
    },
    "productie": {
        "char_front": (
            "{char}. Standing facing camera directly, frontal portrait shot, "
            "modern manufacturing production floor background with conveyor blurred, "
            "bright fluorescent factory lighting, 85mm portrait lens, shallow depth of field, "
            "editorial documentary photography, hyperrealistic 8K, photorealistic"
        ),
        "awareness": (
            "Modern manufacturing facility interior. Production line running with one "
            "operator station visibly unmanned. All other workers present, one gap visible. "
            "Shift supervisor looking at clipboard, stressed expression. "
            "Factory lighting bright and clean. Robotic arms in background. "
            "9:16 portrait format, documentary style, hyperrealistic 8K."
        ),
        "consideration": (
            "{char}. Standing at production line looking at supervisor tablet, "
            "explaining something with engaged natural gestures. "
            "Production line running smoothly behind him. Positive forward energy. "
            "Factory lighting bright. 85mm portrait lens, shallow depth. "
            "9:16 portrait format, hyperrealistic 8K, documentary photography."
        ),
        "conversion": (
            "{char}. Watching production line run at full capacity with satisfied expression. "
            "Supervisor nods approvingly at a skilled operator working at a CNC machine. "
            "Factory clean, modern, well-lit. Sense of competence and stability. "
            "Warm industrial lighting. 9:16 portrait format, hyperrealistic 8K, cinematic."
        ),
    },
    "renewable": {
        "char_front": (
            "{char}. Standing facing camera directly, frontal portrait shot, "
            "wind turbines and green fields background blurred, "
            "bright overcast Dutch daylight, 85mm portrait lens, shallow depth of field, "
            "editorial documentary photography, hyperrealistic 8K, photorealistic"
        ),
        "awareness": (
            "Dramatic aerial shot over an offshore wind farm at dusk. "
            "Massive wind turbines — most spinning, a few visibly stationary. "
            "Maintenance vessel on glowing water below. "
            "Epic scale, environmental beauty mixed with operational urgency. "
            "Teal and amber cinematic color grade. 9:16 portrait format, hyperrealistic 8K."
        ),
        "consideration": (
            "{char}. Standing in renewable energy project office, solar panels and wind turbines "
            "visible through large windows behind him. "
            "Confident, purposeful posture with tablet or phone in hand. "
            "Green and orange color elements in environment. Natural daylight. "
            "85mm portrait, shallow depth. 9:16 portrait format, hyperrealistic 8K."
        ),
        "conversion": (
            "{char}. Descending from a wind turbine service platform, smiling broadly at camera. "
            "Bright sunny day, green Dutch fields in background, turbine blades moving above. "
            "Small team celebrating on the ground below. Achievement and purpose visible. "
            "Orange and green safety gear accents. "
            "9:16 portrait format, hyperrealistic 8K, cinematic uplifting."
        ),
    },
    "sales-b2b": {
        "char_front": (
            "{char}. Standing facing camera directly. Professional office. 9:16 portrait."
        ),
        "awareness": (
            "A cinematic vertical 9:16 shot. Deep navy blue dark background. Floating in the center is a glowing red neon digital counter rapidly spinning numbers upwards, ending around 15000. Glitchy tech effects, glowing embers. High contrast, photorealistic, 85mm lens"
        ),
        "consideration": (
            "Cinematic flight through a futuristic fiber optic data tunnel. Core colors are deep navy blue, glowing neon pink, and bright cyber orange. Glowing data streams flowing rapidly. Minimalist tech aesthetic, very sleek and modern, ray tracing, 8K resolution"
        ),
        "conversion": (
            "A futuristic glassmorphism user interface dashboard floating in a dark navy blue void. Neon pink and orange highlights. A glowing minimalist downward pointing arrow pulses in the center. Sleek geometric design, premium B2B tech feel"
        ),
    },
}

# ── Kling motion prompts (wat de video doet) ──────────────────────────────────
# Gebaseerd op Heijmans BTS kwaliteitsstandaard: shot-specifiek, cinematisch

MOTION_PROMPTS = {
    "oil-gas": {
        "awareness": (
            "Slow cinematic aerial descent over the refinery, camera tilting down. "
            "Steam and exhaust smoke drift lazily between towers. "
            "Amber light deepens as sun drops. Camera transitions with subtle push-in "
            "toward the empty control room window. Interior: empty chair slowly rotates "
            "on its own. Screens glow and flicker. Atmospheric haze drifts. "
            "No motion blur, smooth and deliberate. Haunting, urgent mood. "
            "Cinematic pace, no jump cuts."
        ),
        "consideration": (
            "Engineer at laptop slowly looks up from screen toward camera with intent expression. "
            "Natural subtle hand movement — scrolling, clicking. "
            "Behind him through the window: refinery columns visible in golden haze. "
            "Camera very slow steady push-in, 85mm portrait lens compression. "
            "Confident energy builds. Natural light shifts slightly warmer. "
            "Documentary interview feel, no artificial movement."
        ),
        "conversion": (
            "The two engineers reach toward each other and shake hands firmly. "
            "Both break into genuine satisfied smiles. "
            "Camera slowly pulls back revealing the industrial team in background, "
            "all looking on with quiet pride. Golden hour light intensifies momentarily. "
            "Steam wisps drift past in foreground. Slow deliberate pace. "
            "Cinematic warmth. Celebratory but grounded."
        ),
    },
    "constructie": {
        "awareness": (
            "Camera slowly pushes into the project office window from outside. "
            "Inside: the phone on the table rings, vibrating slightly. "
            "The red-highlighted planner on the screen pulses. "
            "Sticky note flutters faintly from HVAC airflow. "
            "Long afternoon shadow creeps slowly across the blueprints. "
            "No people — emphasizing absence. Slow, deliberate, urgent pace."
        ),
        "consideration": (
            "Engineer at briefing table slowly stands straighter and gestures confidently "
            "toward the blueprint in front of him. Natural strong hand movements — "
            "pointing at plans, tapping the table. "
            "Behind him through the window: a crane swings in the distance. "
            "Camera very slow push-in. Documentary authority. Daylight stays consistent. "
            "Authentic workplace energy. No artificial staging."
        ),
        "conversion": (
            "Engineer points confidently into the distance. Camera slowly arcs around him "
            "in a smooth dolly circle, revealing the completed infrastructure behind. "
            "Team members join the frame naturally, gathering around blueprints. "
            "Golden hour light swells. Sense of scale and accomplishment grows. "
            "Cinematic wide pull-back. Pride and team spirit. No artificial staging."
        ),
    },
    "automation": {
        "awareness": (
            "Subtle handheld camera drift across the workbench — slow, like a documentary B-roll. "
            "The loose wiring harness on the open Rittal cabinet sways imperceptibly from the HVAC. "
            "The laptop screen blinks once — a PLC error notification appears and stays. "
            "The coffee mug steams faintly. The empty stool catches the light. "
            "No people — the absence is the subject. "
            "Camera moves no more than a few centimetres. Quiet, deliberate, real."
        ),
        "consideration": (
            "Engineer's finger traces along a rung of ladder logic on the Siemens TIA Portal screen, "
            "then clicks to run the PLC simulation. His head tilts slightly as he reads the output. "
            "The Siemens or Bachmann PLC module on the bench blinks its status LED. "
            "His other hand picks up a pen and makes a small annotation on the paper schematic. "
            "Subtle handheld camera shake — like a colleague filming on a phone. "
            "Documentary workplace energy. Focused, real, no artificial staging."
        ),
        "conversion": (
            "Camera starts inside the open Rittal cabinet — extreme close-up of the PLC module: "
            "a green status LED pulses once, then goes solid. "
            "Camera slowly pulls back revealing: neat red and blue cable bundles, "
            "labelled terminal blocks, 24V power supply glowing green. "
            "The engineer's hand enters the frame from the right — presses a test button on the PLC. "
            "Cut to the HMI panel on the cabinet door: yellow STARTING fades to solid green RUNNING. "
            "Camera pulls further back to reveal the engineer's face — quiet, focused satisfaction, "
            "not a big smile — the look of someone who knows the job is done right. "
            "A colleague off-frame says something; the engineer gives a small nod. "
            "Handheld documentary feel. No fanfare. Real craftsmanship."
        ),
    },
    "productie": {
        "awareness": (
            "Production line continues moving — the gap at the unmanned station "
            "passes through frame in slow motion. Other workers glance at it. "
            "Supervisor looks down at clipboard, exhales slowly. "
            "Camera slowly pushes in on the empty station. "
            "Fluorescent lights hum. Conveyor moves relentlessly. "
            "Documentary pace, no staging. Absence as subject."
        ),
        "consideration": (
            "Supervisor gestures naturally at the tablet screen, "
            "pointing to figures and nodding. Confident engaged body language. "
            "Production line hums in background — steady and productive. "
            "Camera slow push-in. Factory lighting bright and consistent. "
            "Forward momentum. No artificial staging. Real workplace energy."
        ),
        "conversion": (
            "Supervisor and CNC operator share a brief genuine nod of mutual respect. "
            "The machine runs perfectly. Camera pulls back slowly revealing "
            "the full production floor operating at capacity. "
            "Workers focused at each station. Smooth, competent rhythm. "
            "Warm fluorescent light. Pride in craft. Cinematic pull-back pace."
        ),
    },
    "renewable": {
        "awareness": (
            "Camera slowly descends toward the stationary turbines, "
            "passing spinning neighbors — contrast of motion and stillness. "
            "Waves below catch golden dusk light. "
            "Maintenance vessel bobs gently, waiting. "
            "Cut to: planning screen closeup — 'ENGINEER VACANCY' text pulses. "
            "Epic scale and urgency build together. Cinematic teal-amber grade. "
            "No jump cuts. Atmospheric, environmental beauty."
        ),
        "consideration": (
            "Engineer glances from his phone to the window behind him — "
            "wind turbines turning steadily in the distance. "
            "He turns back to camera with purposeful nod. "
            "Behind him: turbines continue rotating, green fields visible. "
            "Camera very slow push-in. Daylight warm and consistent. "
            "Purpose and possibility in his expression. Documentary feel."
        ),
        "conversion": (
            "Engineer reaches the ground level, steps away from the turbine base. "
            "Broad natural smile as he looks at camera. "
            "Team below reacts with genuine satisfaction — fist bumps, shoulder pats. "
            "Above them: turbine blades complete a full rotation. "
            "Camera slowly pulls back revealing the full wind farm landscape. "
            "Sun breaks through clouds momentarily. Uplifting, purposeful. "
            "Bright organic light. Authentic celebration."
        ),
    },
    "sales-b2b": {
        "awareness": (
            "The neon numbers shatter into flying glass particles towards the camera. Bright pink light bursts from behind."
        ),
        "consideration": (
            "Fast continuous forward movement flying through the neon data tunnel. Light streaks zooming past."
        ),
        "conversion": (
            "The dashboard hovers smoothly. The neon arrow pulses with bright light."
        ),
    },
}


def get_image_prompt(sector: str, scene: str, bedrijfsnaam: str = "") -> str:
    """
    Geeft de Leonardo image prompt terug voor sector + scene.
    scene: 'char_front' | 'awareness' | 'consideration' | 'conversion'
    """
    sector = sector.lower().replace(" ", "-").replace("_", "-")
    prompts = IMAGE_PROMPTS.get(sector, {})
    template = prompts.get(scene, "")
    char = CHARACTER_DNA.get(sector, CHARACTER_DNA["constructie"])
    return template.replace("{char}", char).replace("{bedrijf}", bedrijfsnaam)


def get_motion_prompt(sector: str, scene: str) -> str:
    """
    Geeft de Kling motion prompt terug voor sector + scene.
    scene: 'awareness' | 'consideration' | 'conversion'
    """
    sector = sector.lower().replace(" ", "-").replace("_", "-")
    return MOTION_PROMPTS.get(sector, {}).get(scene, "")


def list_sectors():
    return list(IMAGE_PROMPTS.keys())


def list_scenes():
    return ["awareness", "consideration", "conversion"]


if __name__ == "__main__":
    # Preview
    sector = "constructie"
    for scene in ["awareness", "consideration", "conversion"]:
        print(f"\n=== {sector.upper()} / {scene} ===")
        print(f"\nIMAGE PROMPT:\n{get_image_prompt(sector, scene)[:200]}...")
        print(f"\nMOTION PROMPT:\n{get_motion_prompt(sector, scene)[:200]}...")
