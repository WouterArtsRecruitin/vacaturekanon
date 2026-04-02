# Creative Specificaties — Vacaturekanon

## Formaten

### Static Image Ads
| Formaat | Afmeting | Gebruik |
|---------|----------|---------|
| Feed (1:1) | 1080x1080px | Facebook + Instagram Feed |
| Portrait (4:5) | 1080x1350px | Instagram Feed (meer schermruimte) |
| Stories/Reels (9:16) | 1080x1920px | Instagram + Facebook Stories |
| Carousel kaart | 1080x1080px | Meerdere varianten in 1 ad (max 10) |

### Video Ads
| Formaat | Afmeting | Duur | Gebruik |
|---------|----------|------|---------|
| Feed (1:1) | 1080x1080px | 15-30 sec | Facebook + Instagram Feed |
| Stories/Reels (9:16) | 1080x1920px | 15 sec | Instagram Stories + Reels |
| In-stream | 1920x1080px | max 60 sec | Facebook in-stream |

---

## Design Richtlijnen

### Kleur
- **Vacaturekanon accent:** #E85D04 (oranje) — voor badges, buttons, CTA elementen
- **Opdrachtgever primair:** variabel per klant — voor hero-achtergrond
- **Tekst op donker:** #FFFFFF
- **Tekst op licht:** #111827

### Typography op creatives
- **Functietitel:** Barlow Condensed Bold/ExtraBold, groot (min 48px op 1080px breed)
- **Salaris/details:** Inter Semi-Bold, medium
- **CTA tekst:** Barlow Condensed Bold, goed leesbaar op mobile
- **Max 20% van het beeldoppervlak** mag tekst zijn (Facebook advertentiebeleid)

### Logo plaatsing
- Opdrachtgever logo: linksboven, lichte shadow op drukke achtergronden
- Vacaturekanon badge: rechtsboven klein (20x20px equivalent op 1080px) OF in footer bar
- Altijd voldoende contrast ratio (min 4.5:1 voor AA-toegankelijkheid)

### Veilige zones (Stories/Reels 9:16)
- Bovenste 250px: vrij houden van essentiële elementen (UI-overlap Instagram)
- Onderste 300px: vrij houden van essentiële elementen (swipe-up + profiel-UI)
- Tekst in het midden 1080x1370px gebied

---

## Content Templates

### Type 1: Vacature Highlight
**Structuur:**
- Achtergrond: sector-relevante foto (licentievrij: Unsplash, Pexels) of kleur
- Bovenaan: Opdrachtgever logo
- Midden: Functietitel (groot, bold) + Salaris range (kleiner)
- Onderin: CTA bar in oranje (#E85D04): "Reageer Nu →" + Vacaturekanon badge

**Wanneer:** Directe vacature promotie, conversiegericht

### Type 2: Werkgever Spotlight
**Structuur:**
- Achtergrond: authentieke werkplek foto (bij voorkeur aangeleverd door klant)
- Overlay: semi-transparant verloop onderaan (dark to transparent)
- Onderin: "Bij {{bedrijfsnaam}} werk je aan..." + 3 bullet USPs
- CTA: "Bekijk alle vacatures →"

**Wanneer:** Employer branding, awareness fase

### Type 3: Arbeidsmarktcijfer (data-gedreven)
**Structuur:**
- Achtergrond: clean donker (#111827) of sector gradient
- Groot getal: "67 dagen" (Barlow Condensed 900, wit)
- Subtext: "— zo lang staat een technische vacature gemiddeld open in {{sector}}"
- Onderin: "{{bedrijfsnaam}} vult het in 3 weken. Reageer →"

**Wanneer:** Problem-awareness fase, warm/cold audiences

### Type 4: Testimonial Kaart
**Structuur:**
- Foto medewerker (of gegenereerde avatar) links
- Quote rechts: "Al 8 jaar bij {{bedrijfsnaam}} — de beste beslissing van mijn carriere."
- Naam + functietitel onderaan quote
- Vacaturekanon badge + "Jij ook?" CTA

**Wanneer:** Social proof, consideration fase

---

## Bestandsnamen Conventie

```
VK-[SECTOR]-[TYPE]-[FORMAAT]-[VARIANT].[ext]

Sector codes:
  OG = Oil & Gas
  CI = Constructie & Infra
  PM = Productie & Manufacturing
  AT = Automation & High Tech
  RE = Renewable Energy

Type codes:
  VAC = Vacature Highlight
  EMP = Werkgever Spotlight
  DAT = Arbeidsmarktcijfer
  TST = Testimonial

Formaat codes:
  1080x1080 = 1:1 feed
  1080x1350 = 4:5 portrait
  1080x1920 = 9:16 stories

Variant: A, B, C

Voorbeelden:
  VK-AT-VAC-1080x1080-A.png       (Automation, Vacature, Feed, Variant A)
  VK-OG-EMP-1080x1920-B.mp4       (Oil&Gas, Werkgever, Stories, Video Variant B)
  VK-CI-DAT-1080x1080-A.png       (Constructie, Data, Feed, Variant A)
```

---

## Leveranciers & Tools

### Afbeeldingen
- **Unsplash.com** — gratis, hoge kwaliteit, commercieel gebruik
- **Pexels.com** — gratis, technische/industriele fotos
- **Canva Pro** — templates + tekst overlays + export

### Video
- **Kling AI** — AI video generatie (zie M7 voor prompts)
- **CapCut** — gratis video editing + tekst overlays
- **DaVinci Resolve** — gratis, professionele video editing

### Licentievrije muziek
- **YouTube Audio Library** — gratis, geen attributie vereist
- **Epidemic Sound** — betaald (€15/maand), beste kwaliteit
- **Pixabay Music** — gratis, CC0 licentie

---

## KPI Benchmarks per Formaat

| Formaat | Benchmark CTR | Benchmark CPL | Notitie |
|---------|--------------|--------------|---------|
| Feed 1:1 | 0.8-1.5% | €8-18 | Stabiel, goed schaalbaar |
| Stories 9:16 | 0.5-1.2% | €10-22 | Snel consumeerbaar, swipe-up |
| Reels 9:16 | 1.0-2.5% | €6-14 | Hoogste bereik, laagste CPL |
| Carousel | 1.2-2.0% | €7-15 | Hoge engagement, meer info |

**Actie bij afwijking:**
- CTR <0.5% voor 3+ dagen: refresh creative
- CPL >€25: pause en onderzoek audience overlap
- Frequentie >3 in 7 dagen: vernieuwen creative of audience uitbreiden
