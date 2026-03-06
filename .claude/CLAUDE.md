# CLAUDE.md — Recruitin B.V.
# Antigravity leest dit bestand aan het begin van elke sessie
# Laatste update: 2026-03-04

---

## BEDRIJF

| | |
|---|---|
| **Naam** | Recruitin B.V. |
| **DGA** | Wouter Arts |
| **Locatie** | Doesburg, Gelderland |
| **Focus** | Technisch recruitment — mid-market 50-800 FTE |
| **Sectoren** | Oil & Gas · Constructie · Productie · Automation · Renewable Energy |
| **Regio's** | Gelderland · Overijssel · Noord-Brabant |

---

## HUISSTIJL

```
Primair:    #2D2D2D  (donkergrijs)
Accent:     #E8630A  (oranje)
Fonts:      Bricolage Grotesque (headings) · DM Sans (body)
Toon:       Direct · Zakelijk · Data-gedreven · Geen fluff
```

---

## TECH STACK

| Domein | Tool |
|--------|------|
| Hosting | Vercel (Next.js) · Netlify (static) · Cloudflare Workers (API) |
| CRM | Pipedrive (sales) · Notion (kanban) |
| Forms | Jotform (betalingen) · Typeform (UX) |
| Email | Resend (transactional) · Gmail (outreach) |
| Video generatie | Kling API · InVideo MCP |
| Image generatie | Nano Banana / Imagen 4 (Google) |
| Video editing | InVideo (assembly + voiceover) |
| Outreach | Lemlist |
| Data | Apollo.io · JobDigger · Supermetrics |
| Monitoring | Python cron · Slack webhooks |

---

## API KEYS & CREDENTIALS

```bash
# Kling Video API (officieel — app.klingai.com)
KLING_ACCESS_KEY=Aeyk3t9Re9MtTab8gG4pgfh4f3gBgQAL
KLING_SECRET_KEY=RkfDrMkmmfJ4knQrkt9nYGTf3GB4f3tD
KLING_BASE_URL=https://api.klingai.com

# Overige keys — zie ~/recruitin/.env
ANTHROPIC_API_KEY=zie .env
PIPEDRIVE_API_KEY=zie .env
RESEND_API_KEY=zie .env
SLACK_WEBHOOK_URL=zie .env
JOTFORM_SECRET=zie .env
```

---

## MCP CONNECTORS

| Connector | URL | Status |
|-----------|-----|--------|
| InVideo | https://mcp.invideo.io/sse | ✅ Actief in Claude.ai |
| Notion | https://mcp.notion.com/mcp | ✅ Actief |
| Zapier | https://mcp.zapier.com/api/mcp/... | ✅ Actief |
| Apollo.io | https://mcp.apollo.io/mcp | ✅ Actief |
| Jotform | https://mcp.jotform.com | ✅ Actief |
| Supabase | https://mcp.supabase.com/mcp | ✅ Actief |
| Cloudflare | https://bindings.mcp.cloudflare.com/sse | ✅ Actief |
| Pipedrive | via Zapier MCP | ✅ Actief |

**InVideo MCP tool:** `generate-video-from-script`
Args: `script` · `topic` · `vibe` · `target_audience`

---

## MAPSTRUCTUUR

```
~/recruitin/
├── .claude/
│   └── CLAUDE.md                  ← dit bestand
├── .env                           ← alle API keys
├── scripts/
│   ├── kling_invideo_pipeline.py  ← Kling + InVideo automation
│   ├── meta_campaign_builder.py   ← Meta Marketing API
│   └── kt-daily-monitor.py        ← dagelijkse monitoring
├── landing-pages/
│   └── [campagne]/
│       └── index.html             ← Netlify deploy
├── meta-campaigns/
│   ├── assets/
│   │   └── [campagne]/
│   │       ├── character.png
│   │       ├── visual-1.png
│   │       ├── visual-2.png
│   │       ├── visual-3.png
│   │       └── visual-4.png
│   ├── videos/
│   │   └── [campagne]/
│   │       ├── scene_01.mp4
│   │       ├── scene_02.mp4
│   │       ├── scene_03.mp4
│   │       └── invideo_instructie.md
│   └── [campagne]/
│       ├── campaign-ids.json      ← Meta IDs + Netlify URL
│       └── ad-copy.json
└── kandidatentekort-v2/
    └── worker.js                  ← Cloudflare Worker
```

---

## ACTIEVE PROJECTEN

### P1 — kandidatentekort.nl (KRITISCH)
- **Status:** Automation down sinds augustus 2024
- **Verlies:** €23.970/maand · €167.790 totaal verloren
- **Fix:** Cloudflare Worker v2 (Jotform → Claude rapport → Pipedrive → Resend)
- **Script:** ~/recruitin/kandidatentekort-v2/worker.js

### P2 — Pipedrive Stage 2 Bottleneck
- **Status:** €519k vast in Stage 2 · 65 deals
- **Actie:** Email nurture sequence via Zapier + Lemlist follow-up

### P3 — Meta Campagnes
- **Budget:** €500/maand
- **Campagnes:** KT_[sector]_[jaar] formaat
- **KPIs:** CPL €15-40 (pauzeer >€60) · CTR min 0.8% · Frequentie max 3x

### P4 — Video Pipeline (NIEUW)
- **Stack:** Nano Banana → Kling API → InVideo MCP
- **Script:** ~/recruitin/scripts/kling_invideo_pipeline.py
- **Output:** 3 clips × 5s → InVideo assembly → MP4 feed + Reels

---

## CAMPAGNE AUTOMATION — VOLLEDIGE WORKFLOW

Bij elke nieuwe campagne voert Antigravity deze 5 taken **altijd** uit, in volgorde.
Campagne naamgeving: `KT_[Sector]_[Jaar]` — bijv. `KT_OilGas_2025`

---

### TAAK 1 — CHARACTER IMAGE + AD VISUALS (Nano Banana / Imagen)

**Character DNA (kopieer exact naar elke prompt):**
```
Een begin-40-jarige West-Europese man, donkerbruin haar kort en netjes
gekamt, lichtgeschoren baard, sterke kaaklijnen, donkerblauw werkpak
met subtiel logo op borstzak, zelfverzekerd maar benaderbaar.
85mm portretlens, zachte bokeh, [SECTOR] werkomgeving onscherp achtergrond,
professionele editorial fotografie, hyperrealistisch 8K.
GEEN tekst, GEEN letters, GEEN watermark, GEEN logo in beeld.
```

Genereer altijd 5 bestanden per campagne:
- `character.png` — neutraal portret, basis voor Kling
- `visual-1.png` — gefrustreerd naar laptop (schaarste hook)
- `visual-2.png` — zelfverzekerd, armen gekruist (autoriteit)
- `visual-3.png` — glimlacht ontspannen (social proof)
- `visual-4.png` — wijst naar rechts buiten frame (CTA)

Opslaan in: `~/recruitin/meta-campaigns/assets/[CAMPAGNE]/`

---

### TAAK 2 — LANDING PAGE BOUWEN & DEPLOYEN

Bouw automatisch een high-conversion landing page en deploy op Netlify.
**URL formaat:** `[sector].kandidatentekort.nl`

**Pagina opbouw (altijd dezelfde structuur):**

```
HERO
  H1:  "Is jouw [FUNCTIE] vacature al langer dan 6 weken open?"
  Sub: "[SECTOR] bedrijven in [REGIO] kampen met extreme schaarste.
        Ontvang gratis een analyse — binnen 10 minuten in je inbox."
  CTA: "Vraag gratis analyse aan →" (oranje knop #E8630A)

STATISTIEKEN BALK
  7/10 schaars | 4,5 maanden doorlooptijd | €18.400 kosten/jaar

HOE HET WERKT (3 stappen)
  1. Vul formulier in (2 min)
  2. Systeem analyseert arbeidsmarkt
  3. Rapport automatisch in inbox

SOCIAL PROOF
  Quote + sector bedrijfs-logo placeholders

JOTFORM EMBED
  URL: [JOTFORM_URL]?utm_source=lp&utm_campaign=[CAMPAGNE]

FOOTER
  kandidatentekort.nl | Recruitin B.V. | Doesburg
```

**Technische vereisten:**
```
Stack     : Vanilla HTML/CSS/JS — één bestand
Huisstijl : bg #060708 · surface #0C0E13 · oranje #E8630A · tekst #DDE0EE
Fonts     : Bricolage Grotesque (headings) · DM Sans (body)
Pixel     : fbq('init', '[META_PIXEL_ID]') + Lead event op form submit
Scroll    : fbq('track', 'ViewContent') op 50%
Mobile    : Mobile-first, Lighthouse >90
```

**Deploy commando:**
```bash
netlify deploy --prod \
  --dir=~/recruitin/landing-pages/[CAMPAGNE] \
  --site=[NETLIFY_SITE_ID]
```

Sla live URL op in `campaign-ids.json` voor gebruik in Meta campagne.

---

### TAAK 3 — META CAMPAGNE AANMAKEN (Marketing API v21.0)

Maak via de Meta Marketing API een volledige campagne structuur aan.
**Status altijd: PAUSED** — Wouter activeert handmatig na review.

**Campagne structuur:**
```
Campaign: KT_[Sector]_[Jaar] | Objective: LEAD_GENERATION | PAUSED

Ad Set 1 — Prospecting (60% budget)
  Targeting: HR Manager · HR Director · DGA · CEO · Directeur
  Bedrijfsgrootte: 50-800 FTE | Geo: Gelderland/Overijssel/Noord-Brabant

Ad Set 2 — Lookalike (25% budget)
  Source: kandidatentekort.nl pixel bezoekers 180 dagen
  Lookalike: 1% Nederland

Ad Set 3 — Retargeting (15% budget)
  Audience: site bezoekers 30d MINUS Pixel Lead events
```

**4 ad varianten per ad set (op basis van sector/functie):**
```
Variant 1 — Schaarste:   "[FUNCTIE] vinden in [SECTOR]? Score: X/10 schaars"
Variant 2 — Kosten:      "Wat kost een open [FUNCTIE] vacature per maand?"
Variant 3 — Social proof: "6 weken. 3 kandidaten. [SECTOR], [REGIO]."
Variant 4 — Urgentie:    "Jouw concurrent werft al. Ben jij er klaar voor?"
```

**UTM structuur (altijd meegeven):**
```
?utm_source=meta&utm_medium=paid&utm_campaign=[CAMPAGNE]&utm_content=[VARIANT]
```

Alle IDs opslaan in: `~/recruitin/meta-campaigns/[CAMPAGNE]/campaign-ids.json`

---

### TAAK 4 — KLING VIDEO CLIPS

```bash
python3 ~/recruitin/scripts/kling_invideo_pipeline.py \
  --image ~/recruitin/meta-campaigns/assets/[CAMPAGNE]/character.png \
  --campagne [CAMPAGNE] \
  --sector "[SECTOR]" \
  --duur 5 \
  --formaat 1:1
```

Opties: `--duur 5|10` · `--formaat 1:1|9:16|16:9` · `--test-auth` · `--dry-run`

**Scene structuur (altijd):**
| Scene | Inhoud | Emotie | Licht |
|-------|--------|--------|-------|
| 1 (0-5s) | Open vacature kost geld | Gefrustreerd | Koel, gedesatureerd |
| 2 (5-10s) | Recruitin analyseert gratis | Ontdekking | Warmer |
| 3 (10-15s) | kandidatentekort.nl | Zelfverzekerd | Warm oranje |

---

### TAAK 5 — INVIDEO ASSEMBLY (Claude.ai)

Na Kling: lees `invideo_instructie.md` → print inhoud → Wouter kopieert naar Claude.ai met InVideo MCP aan.
Tool: `generate-video-from-script`
Output: MP4 feed (1080×1080) + Reels (1080×1920)

---

## IMAGE FRAMEWORK — VASTE REGELS

```
NOOIT:  Tekst/letters/cijfers in Nano Banana prompt
NOOIT:  Automatische prompt generatie door AI
NOOIT:  Close-up handen
NOOIT:  Meer dan 1 persoon in beeld
NOOIT:  Andere kleding dan beschreven in Character DNA

ALTIJD: Tekst achteraf toevoegen via Canva
ALTIJD: Negatieve prompt meegeven
ALTIJD: 85mm lens voor gezichten
ALTIJD: Character DNA blok kopiëren aan begin van prompt
ALTIJD: Test 512px eerst — daarna pas full res
```

**Vaste negatieve prompt (altijd toevoegen):**
```
geen tekst, geen letters, geen woorden, geen cijfers,
geen watermark, geen logo in beeld, geen AI-artefacten,
geen vervorming, geen extra vingers, geen dubbele ledematen,
geen plasticachtig uiterlijk, fotorealistisch, geen AI-gevoel,
geen stockfoto-uitstraling, naturel documentaire stijl
```

---

## META CAMPAGNE STRUCTUUR

```
Campagne naam: KT_[Sector]_[Jaar]  (bijv. KT_OilGas_2025)

Ad Set 1 — Prospecting (60% budget)
  Targeting: HR Manager, HR Director, DGA, CEO
  Company size: 50-800 FTE
  Industries: [sector]
  Geo: Gelderland / Overijssel / Noord-Brabant

Ad Set 2 — Lookalike (25% budget)
  Source: kandidatentekort.nl bezoekers 180d
  Lookalike: 1%, Nederland

Ad Set 3 — Retargeting (15% budget)
  Audience: site bezoekers 30d MINUS Pixel Lead events

UTM formaat:
  ?utm_source=meta&utm_medium=paid
  &utm_campaign=[CAMPAGNE]&utm_content=[AD_NAAM]
```

---

## KPI TARGETS

| Metric | Goed | Actie bij overschrijding |
|--------|------|--------------------------|
| CPL | €15-40 | Pauzeer ad set bij >€60 |
| CTR | >0.8% | Ververs creative bij <0.5% voor 3+ dagen |
| Frequentie | <3x/week | Roteer audiences bij >4 |
| Rapport generatie | <60s | Check Cloudflare Worker logs |
| Lemlist open rate | >45% | — |
| Lemlist reply rate | >8% | — |

---

## DOELGROEPEN

**Primair:** HR Manager · HR Director · Talent Acquisition
**Secundair:** DGA · CEO · Directeur · Operations Manager
**Bedrijfsgrootte:** 50-800 FTE
**Sectoren:** Oil & Gas · Constructie · Productie · Automation · Renewable Energy
**Regio:** Gelderland · Overijssel · Noord-Brabant

---

## ANTIGRAVITY AGENT INSTRUCTIES

**Bij elke nieuwe campagne — altijd in deze volgorde:**
1. Lees dit CLAUDE.md volledig
2. Maak mapstructuur aan
3. TAAK 1 → Character image + 4 ad visuals
4. TAAK 2 → Landing page bouwen + deployen op Netlify
5. TAAK 3 → Meta campagne aanmaken via Marketing API (PAUSED)
6. TAAK 4 → Kling video clips genereren
7. TAAK 5 → invideo_instructie.md printen voor Wouter
8. Sla alle IDs en URLs op in campaign-ids.json
9. Stuur Slack notificatie bij voltooiing

**Vaste regels:**
- Campagnes ALTIJD als PAUSED aanmaken — nooit direct ACTIVE
- Nooit tekst in image prompts — altijd post via Canva
- `--test-auth` draaien voor eerste Kling run van de dag
- Wacht op bevestiging per taak voor je verdergaat
- Bij Kling clip failure: automatisch retry (max 2x)

---

## SNELLE COMMANDO'S

```bash
# Kling auth testen
python3 ~/recruitin/scripts/kling_invideo_pipeline.py --test-auth

# Nieuwe video campagne (dry run eerst)
python3 ~/recruitin/scripts/kling_invideo_pipeline.py \
  --dry-run --campagne KT_[SECTOR]_2025 --sector "[SECTOR]"

# Monitoring draaien
python3 ~/recruitin/scripts/kt-daily-monitor.py

# Cloudflare Worker deployen
cd ~/recruitin/kandidatentekort-v2 && wrangler deploy
```

---

## CAMPAGNE AUTOMATION — TRIGGER FLOW

```
kandidatentekort.nl Jotform submit
    ↓
Zapier webhook → Antigravity
    ↓
TAAK 1: Character image + 4 ad visuals (Nano Banana)
TAAK 2: Dynamische landing page per sector (Netlify)
         URL: [sector-slug].kandidatentekort.nl
TAAK 3: Meta campagne (Marketing API v21.0) — PAUSED
TAAK 4: Kling video clips (pipeline script)
TAAK 5: Eindrapport + Slack
    ↓
Jij: InVideo assembly (Claude.ai, 2 min) + campagne activeren
```

## SECTOR → SUBDOMAIN MAPPING

| Sector | Subdomain | Schaarste |
|--------|-----------|-----------|
| oil & gas | oilgas.kandidatentekort.nl | 8.5/10 |
| constructie | constructie.kandidatentekort.nl | 9.1/10 |
| automation | automation.kandidatentekort.nl | 9.4/10 |
| productie | productie.kandidatentekort.nl | 7.8/10 |
| renewable energy | renewable.kandidatentekort.nl | 9.7/10 |

## SCRIPTS OVERZICHT

| Script | Gebruik |
|--------|---------|
| `kling_invideo_pipeline.py` | Kling clips genereren |
| `meta_campaign_builder.py` | Meta campagne via API |
| `kt-daily-monitor.py` | Dagelijkse KPI monitoring |

## KAMPAGNE NAAMGEVING

```
KT_[sector-slug]_[YYYYMM]
KT_OilGas_202603
KT_Constructie_202603
KT_Automation_202603
```
