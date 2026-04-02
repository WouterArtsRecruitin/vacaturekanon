# Nano Banana / Imagen 4 Image Prompts
## Vacaturekanon — Demo Sector: Automation & High Tech
## Gegenereerd: 2026-03-09

> Kopieer elk prompt blok 1-op-1 naar Nano Banana of Imagen 4.
> Genereer altijd 512px versie eerst als test, dan full res.
> Voeg tekst toe via Canva (NOOIT in de AI prompt).

---

## CHARACTER DNA (kopieer dit blok aan het begin van ELKE prompt)

```
A man in his early 40s, Western European, dark brown hair neatly combed short,
light trimmed beard, strong jawline, dark navy work jacket with subtle logo pocket,
confident yet approachable expression. 85mm portrait lens, soft bokeh background,
automation factory environment out of focus behind him, professional editorial
photography, hyperrealistic 8K.
NO text, NO letters, NO watermark, NO logo visible in image.
```

---

## VASTE NEGATIEVE PROMPT (altijd toevoegen)

```
no text, no letters, no words, no numbers, no watermark, no logo in image,
no AI artifacts, no distortion, no extra fingers, no double limbs,
no plastic appearance, photorealistic, no AI feeling, no stock photo look,
natural documentary style
```

---

## character.png — Neutraal portret (basis voor Kling)

**Positieve prompt:**
```
[CHARACTER DNA]
Neutral expression, looking directly at camera with quiet confidence.
Background: blurred PLC control panels and automation equipment, soft blue-amber
industrial lighting. Half-body portrait, arms slightly relaxed at sides.
Clean, corporate but technical atmosphere.
```

**Gebruik:** Input voor Kling image-to-video pipeline

---

## visual-1.png — Gefrustreerd (schaarste hook)

**Positieve prompt:**
```
[CHARACTER DNA]
Frustrated expression, both hands on forehead, leaning over a standing desk.
Multiple monitors behind him showing error messages and vacancy dashboards.
Calendar on wall showing 71 days circled in red. Amber warning lights from
PLC panels casting dramatic shadows. Body language: overwhelmed, under pressure.
```

**Tekst overlay (Canva):**
- Hoofdtekst: "71 dagen. Nog steeds geen PLC-programmeur."
- Sub: "3,8 vacatures per werkzoekende in automation"
- CTA: "Gratis analyse → vacaturekanon.nl"

---

## visual-2.png — Zelfverzekerd, armen gekruist (autoriteit)

**Positieve prompt:**
```
[CHARACTER DNA]
Arms crossed, upright posture, confident direct gaze at camera. Slight smile.
Background: modern automation control room, robotic arms visible and in motion
(blurred), multiple screens showing live production data. Professional lighting:
warm key light from left, cool fill from screens. Authority and competence.
```

**Tekst overlay (Canva):**
- Hoofdtekst: "Van vacature naar aanname: 18 dagen"
- Sub: "Vacaturekanon — recruitment automation voor technische bedrijven"

---

## visual-3.png — Glimlacht ontspannen (social proof)

**Positieve prompt:**
```
[CHARACTER DNA]
Relaxed, genuine smile, slightly turned 3/4 toward camera. One hand casually
holding a tablet showing a recruitment dashboard with green checkmarks.
Background: open-plan engineering office with technical drawings on glass walls,
colleagues working at desks (blurred). Warm, approachable energy. Natural light
from large windows mixing with screen glow.
```

**Tekst overlay (Canva):**
- Quote: "Binnen 3 weken onze automation engineer gevonden. Eindelijk."
- Naam: "Operations Director, Machinebouwbedrijf Gelderland"
- Logo: Vacaturekanon (rechtsonder)

---

## visual-4.png — Wijst naar rechts (CTA)

**Positieve prompt:**
```
[CHARACTER DNA]
Right arm extended, pointing decisively to the right out of frame. Energetic,
forward momentum. Eye contact with camera, confident expression. Background:
split view — left side: automation factory floor with robotic arms; right side:
blurred bright light suggesting the "answer" or solution. Dynamic composition,
sense of direction and purpose. Orange accent light from right side.
```

**Tekst overlay (Canva):**
- Hoofdtekst: "Jouw volgende automation engineer zit hier →"
- CTA button: "Gratis analyse aanvragen" (oranje #E85D04)
- URL: vacaturekanon.nl

---

## Technische specs per afbeelding

| Spec | Waarde |
|------|--------|
| Formaat feed | 1080 × 1080 px (1:1) |
| Formaat Stories/Reels | 1080 × 1920 px (9:16) |
| Formaat Carousel | 1080 × 1080 px |
| Kleurprofiel | sRGB |
| Max bestandsgrootte | 30 MB |
| Test formaat | 512 × 512 px eerst |

## Opslaan als

```
~/recruitin/meta-campaigns/assets/KT_Automation_202603/
├── character.png     ← Kling input
├── visual-1.png      ← Meta Ad schaarste hook
├── visual-2.png      ← Meta Ad autoriteit
├── visual-3.png      ← Meta Ad social proof
└── visual-4.png      ← Meta Ad CTA
```

---

## Workflow na image generatie

1. **character.png** → Kling pipeline (zie stap hieronder)
2. **visual-1 t/m 4** → Canva voor tekst overlays → export als PNG
3. Upload alle 5 bestanden naar `~/recruitin/meta-campaigns/assets/KT_Automation_202603/`
4. Start Kling (na saldo bijstorten):

```bash
cd ~/recruitin && python3 scripts/kling_invideo_pipeline.py \
  --image ~/recruitin/meta-campaigns/assets/KT_Automation_202603/character.png \
  --campagne KT_Automation_202603 \
  --sector "automation" \
  --regio "Gelderland" \
  --duur 5 \
  --formaat 9:16
```

Kling genereert dan 3 video scenes op basis van character.png.
