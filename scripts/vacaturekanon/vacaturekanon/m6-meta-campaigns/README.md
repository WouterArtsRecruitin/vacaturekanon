# M6 — Meta Campaign Configuration

Alles wat je nodig hebt om Meta (Facebook/Instagram) campagnes op te zetten voor Vacaturekanon-klanten.

## Bestanden

| Bestand | Inhoud |
|---------|--------|
| `campaign-config.json` | Audience targeting per sector (5 sectoren) |
| `ad-copy-varianten.md` | 3 ad copy varianten per sector (15 totaal) |
| `creative-specs.md` | Formaten, design richtlijnen, bestandsnamen |

## Campagne aanmaken — stap voor stap

### 1. Meta Ads Manager openen
Ga naar ads.meta.com → Campagnes → "+ Aanmaken"

### 2. Campagne niveau
- Doel: **Leads** (niet Verkeer of Bereik)
- Naam: `VK-[SECTOR]-[bedrijfsnaam]` (bijv. `VK-AT-TechflowBV`)
- Budget: Campagnebudget op (CBO) — laat Meta verdelen
- Status: **PAUSED** — activeer pas na review

### 3. Ad Set niveau (3 ad sets per campagne)

**Ad Set 1: Breed (60% budget)**
- Audience: Kopieer interests uit `campaign-config.json` voor de sector
- Geo: Gelderland + Overijssel + Noord-Brabant (+ optioneel 40km radius)
- Leeftijd: zie config per sector
- Placements: Advantage+ placements (laat Meta optimaliseren)

**Ad Set 2: Retargeting (25% budget)**
- Audience: Custom audience → Pixel → Website bezoekers 30 dagen
- Exclusie: Mensen die al Lead event getriggerd hebben
- Placements: Advantage+ placements

**Ad Set 3: Lookalike (15% budget)**
- Audience: Lookalike 1% NL op basis van Lead pixel events
- Activeer pas als er 50+ Lead events in de bron zijn

### 4. Ad niveau

Per ad set: 3 ads aanmaken (Variant A, B, C uit `ad-copy-varianten.md`)

- Kies het juiste creative formaat (zie `creative-specs.md`)
- Vul primary text, headline en description in
- Kies CTA button
- Voer landingspagina URL in + UTM parameters

**UTM structuur:**
```
?utm_source=meta&utm_medium=paid
&utm_campaign=VK-[SECTOR]-[bedrijfsnaam]
&utm_content=[variant-A/B/C]
&utm_term=[ad-set-naam]
```

### 5. Pixel verificatie

Controleer voor publicatie:
1. Meta Pixel Helper (Chrome extensie) installeren
2. Open de landingspagina van de klant
3. Verifieer: PageView event vuurt
4. Klik op CTA → verifieer: Lead event vuurt

### 6. Budget optimalisatie

**Start:** €20-30/dag voor de eerste 7 dagen (learningfase)
**Na 7 dagen:** Evalueer op CPL:
- CPL <€15: schaal op met 20% per 3 dagen
- CPL €15-25: handhaven, optimaliseer creative
- CPL >€25: pause slechtste ad set, budget naar winnaar
- CPL >€40: stop campagne, reviseer targeting

### 7. Rapportage

Wekelijks rapport voor de klant:
- Bereik + Impressies
- Klikken + CTR
- Leads + CPL
- Top performing ad (variant)
- Aanbeveling komende week

Gebruik het KPI dashboard in M10 voor overzicht.
