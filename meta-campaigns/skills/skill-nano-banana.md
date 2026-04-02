# Skill: Nano Banana Visual Generatie

## Doel
4 PNG visuals genereren (1080x1080px) voor Meta Ads feed.
Elke visual correspondeert met een ad copy variant (schaarste / kosten / social_proof / urgentie).

---

## Meta Ads Visual Specs

| Spec | Waarde |
|------|--------|
| Formaat | PNG (voorkeur) of JPG |
| Dimensies | 1080 x 1080 px (1:1) |
| Max bestandsgrootte | 30 MB |
| Min bestandsgrootte | >10 KB |
| Kleurruimte | sRGB |
| Tekst op visual | Max 20% van oppervlak (anders bereik beperkt) |
| Veilige zone | 50px marge rondom voor cropping |

---

## 4 Visual Types + Gemini Image Gen Prompts

### Visual 1 — Schaarste
**Doel:** Exclusiviteit + FOMO
**Stijl:** Professionele vakmens in actie, subtiel schaars/premium gevoel

```
Gemini Prompt:
"Professional Dutch tradesman [functie] working on [sector] site, confident posture,
high-quality equipment, industrial background. Photorealistic, square 1:1 composition,
dramatic lighting, dark navy and orange color palette. Text overlay space at bottom 20%.
No text in image. Cinematic quality, Dutch industrial aesthetic."
```

**Nano Banana parameters:**
- Stijl: Fotorealistisch / Editorial
- Kleur: Navy #1B2A4A + Oranje accent #FF6B00
- Tekst in visual: "Exclusief voor {functie}s met {X}+ jaar ervaring"
- Positie tekst: Onderin, witte tekst op donkere overlay

---

### Visual 2 — Kosten (salaris/voordelen)
**Doel:** Financieel aantrekkelijk, concreet
**Stijl:** Lifestyle + zekerheid, thuiskomen na goede dag werken

```
Gemini Prompt:
"Happy Dutch professional tradesman arriving home, modern car in driveway, relaxed smile,
casual professional clothing. Warm golden hour lighting, suburban Dutch neighborhood.
Square 1:1 composition. Text space reserved at bottom 25%. Photorealistic, aspirational mood."
```

**Nano Banana parameters:**
- Stijl: Warm, aspirationeel
- Kleur: Warm groen #2D7D46 + Wit
- Tekst in visual: "€{min} - €{max} bruto/jaar + lease auto"
- Positie tekst: Bovenin, donkere overlay

---

### Visual 3 — Social Proof
**Doel:** Vertrouwen via bewijs van anderen
**Stijl:** Groep vaklieden, team gevoel, professioneel

```
Gemini Prompt:
"Group of 5 Dutch male and female industrial workers in safety gear, smiling confidently,
construction or industrial site background, professional team photo composition.
Square 1:1 format, text space at bottom. Warm lighting, trust-inspiring, documentary style."
```

**Nano Banana parameters:**
- Stijl: Documentair / Authentiek
- Kleur: Blauw #0056A3 + Wit
- Tekst in visual: "{aantal}+ vakmensen gingen je voor"
- Icoon: Ster-rating of checkmarks

---

### Visual 4 — Urgentie
**Doel:** Nu actie ondernemen, niet wachten
**Stijl:** Timer-gevoel, decisief moment, countdown energie

```
Gemini Prompt:
"Dutch industrial worker making a decisive phone call or checking phone, sense of urgency,
clean professional background, dramatic side lighting, square 1:1 composition.
Deep red and dark background, action-oriented composition. Text space at bottom 20%."
```

**Nano Banana parameters:**
- Stijl: Dramatisch, urgentie
- Kleur: Rood #CC2929 + Donker #1A1A1A
- Tekst in visual: "Vacature sluit binnenkort"
- Element: Countdown timer icoon of pijl

---

## Bestandsnamen (verplicht voor Agent 02)

```
campaigns/{campagne_naam}/assets/schaarste.png
campaigns/{campagne_naam}/assets/kosten.png
campaigns/{campagne_naam}/assets/social_proof.png
campaigns/{campagne_naam}/assets/urgentie.png
```

---

## Workflow

1. **Genereer** via Nano Banana / Gemini Image Gen (4 visuals per campagne)
2. **Exporteer** als PNG 1080x1080px
3. **Sla op** in `campaigns/{campagne}/assets/`
4. **Valideer** met Agent 02: `python3 agents/agent-02-visual-validator.py --campagne {naam}`

---

## Kleurpaletten per sector

| Sector | Primair | Accent | Stijl |
|--------|---------|--------|-------|
| Oil & Gas | #1B3A5C (navy) | #FF8C00 (oranje) | Industrieel, krachtig |
| Constructie | #2C4A1E (donkergroen) | #F4A400 (geel) | Aards, solide |
| Productie | #3D3D3D (antraciet) | #00A6FF (blauw) | Precies, high-tech |
| Automation | #0D1B2A (bijna zwart) | #00E5FF (cyan) | Futuristisch, tech |
| Renewable Energy | #1A5C3A (groen) | #FFD700 (goud) | Duurzaam, positief |

---

## Tips

- **Geen stockfoto-gevoel** — gebruik echte of realistische Nederlandse setting
- **Geen tekst in de afbeelding** naast de geplande overlay (Meta tekst-regel)
- **Test op mobiel** — 90% Meta traffic is mobiel; tekst moet leesbaar zijn op 375px breed
- Genereer altijd 2-3 varianten per type en kies de beste
