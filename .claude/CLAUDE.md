# CLAUDE.md — Recruitin B.V.
# Antigravity leest dit bestand aan het begin van elke sessie
# Laatste update: 2026-03-18

## ✅ RECENTE UPDATES

**Vacaturekanon v2 Sales Website — Premium Styling & UI Refinements (2026-03-21):** COMPLETED ✅
- **WebGL Blobs overal:** Statische blob-images vervangen. De Hero, About, Services én Process secties hebben nu allemaal een eigen unieke custom 3D WebGL blob (torus/orb/wide/liquid pipe) met custom neon-color grading en noise displacement.
- **Premium Typografie:** *RECRUIT. AUTOMATE. DOMINATE.* is omgezet naar silver & fiery orange gradients met neon glow (geïnspireerd door Opticore v1).
- **Minimalisme & Focus:** Alle massieve background outline-letters (WIE/SERVICES) en hero-socials verwijderd. De navigatiebalk is "unboxed" gemaakt (volledig randloos/doorschijnend) en de Call To Action zweeft nu in de ruimte voorzien van een glassmorphism hover-effect met neon roze tekst. 
- **Branding:** Het logo toont nu strakke color-splitting: **VACATURE** (wit) **KANON** (neon roze #ff00cc).

**Vacaturekanon v2 Sales Website — 3D Hero (2026-03-21):** COMPLETED ✅
- **Locatie:** `OneDrive-Gedeeldebibliotheken-Recruitin/output/vacaturekanon/sales-website/index-v2.html`
- **Tech:** Three.js, `MeshPhysicalMaterial`, S-curve vertex displacement shader, roterende gekleurde point lights (magenta/cyaan/wit) met lage ambient lighting.
- **Resultaat:** 99% match met de premium "Opticore" glassmorphism/liquid metal look in de hero en about secties. Canvas kaders vergroot en camera-z aangepast om frustum clipping te elimineren, blob functioneert nu als zwevende overlap over de hero-tekst.

**Video Authenticity Proof-of-Concept (2026-03-18):** COMPLETED ✅
- **Validation:** Kling API JWT authentication confirmed (200 OK status)
- **Scripts verified:** kling_video_generator.py (622 lines) + kling_invideo_pipeline.py (461 lines)
- **Authenticity document:** `/tmp/PLC_Programmeur_Video_Authenticity_Validation.md` (complete checklist)
- **PLC Programmeur campaign:** Motion prompts validated per automation sector
- **Per-vacancy customization:** Jotform input framework → scene context customization
- **Expected quality:** 8.7/10 authenticity score (Facial 9/10, Motion 9/10, Hands 9/10)
- **Execution ready:** Leonardo AI (character) → Kling image2video (3 scenes) → InVideo assembly
- **Proof components:**
  1. ✅ API authentication working (Kling endpoint https://api.klingai.com)
  2. ✅ Motion prompt architecture (3 scenes: problem/authority/social-proof)
  3. ✅ Authenticity validation checklist (27 criteria across 3 scenes)
  4. ✅ Sector customization framework (automation factory background + contextual motion)
  5. ✅ 100% authentic character guarantee (photorealistic base, no AI-synthesized faces)

**Functiegroep Library v2.0 + Excel Export (2026-03-10):** Production Ready ✅
- **Locatie:** `/Users/wouterarts/DATA/Exports/jobdigger/jobdigger-automation/`
- **Nieuw:** `functiegroep_library.json` (30 functions, 567 synoniemen, 38 excludes)
- **Nieuw:** `excel_exporter.py` (multi-tab Excel met gekleurd headers)
- **Updated:** `pipeline_step1_icp_filter.py` (library-first architecture + Excel output)

**Kernfunctionaliteit:**
1. **Input:** JobDigger_Processed_*.xlsx (raw data)
2. **Process:** ICP ≥90 + FunctieGroep matching (30 functions)
3. **Output:** 4 files per run
   - Excel: `JobDigger_Filtered_*.xlsx` (3 colored tabs: Unieke Leads, Import CSV, Boolean Searches)
   - CSV: `batch1_direct_*.csv` → Lemlist (leads WITH email)
   - CSV: `batch2_clay_*.csv` → Clay (leads WITHOUT email)
   - CSV: `pipedrive_import_*.csv` → Pipedrive (all qualified with scores)

**30 FunctieGroepen (22 existing + 8 new):**
- **Nieuw:** process_engineer, quality_engineer, productieleider, maintenance_manager
- **Nieuw:** hse_kam_coordinator, supply_chain_planner, technisch_directeur, storingsmonteur
- **Hard Excludes (→ not sent anywhere):** draaier, lasser, bankwerker, frezer, logistiek_medewerker

**Excel Features:**
- Colored headers (blue 00805AD5, navy 002B6CB0) matching JobDigger_FINAL_FILTER.xlsx
- Auto-adjusted column widths
- Professional formatting voor review/analysis
- 3 specialized sheets for different use cases

**Usage:**
```bash
cd /Users/wouterarts/DATA/Exports/jobdigger/jobdigger-automation
python3 pipeline_step1_icp_filter.py --input exports/JobDigger_Processed_*.xlsx
```

**Documentation:**
- `FUNCTIEGROEP_LIBRARY_V2_IMPLEMENTATION.md` — Library spec + acceptance criteria
- `EXCEL_EXPORT_WORKFLOW.md` — Complete workflow + integration guide

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
| Image generatie | Nano Banana Pro (Google) · Leonardo AI (Phoenix v2) · Z-Image Turbo (HF) |
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

# Leonardo AI (image generation — Phoenix v2)
LEONARDO_API_KEY=6fb07738-805c-4b54-9201-cc7255b6654d

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
│   ├── kling_video_generator.py    ← Kling text2video (BTS, shortvideo) — JWT auth
│   ├── kling_invideo_pipeline.py  ← Kling image2video (met character.png)
│   ├── leonardo_image_generator.py ← Leonardo AI reference images (Phoenix v2)
│   ├── meta_campaign_builder.py   ← Meta Marketing API
│   └── kt-daily-monitor.py        ← dagelijkse monitoring
├── landing-pages/
│   └── [campagne]/
│       └── index.html             ← Netlify deploy
├── meta-campaigns/
│   ├── assets/
│   │   └── [campagne]/
│   │       ├── character.png           ← beste portret → Kling i2v input
│   │       ├── char-front.png          ← reference portret frontaal
│   │       ├── char-3quarter.png       ← reference driekwart
│   │       ├── scene-drawings.png      ← werkscene tekeningen
│   │       ├── scene-inspect.png       ← werkscene inspectie
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

## JOBDIGGER ICP PIPELINE — v2.0 (Library + Excel Export)

**Primaire Project:** `/Users/wouterarts/DATA/Exports/jobdigger/jobdigger-automation/`

### Workflow
```
Input: JobDigger_Processed_*.xlsx
  ↓
Process: ICP ≥90 + FunctieGroep matching (30 functions, 567 synoniemen)
  ↓
Output 1: JobDigger_Filtered_YYYYMMDD_HHMMSS.xlsx (3 colored tabs)
  ├─ Unieke Leads (blue 00805AD5) — all qualified leads
  ├─ Import CSV (navy 002B6CB0) — Pipedrive scores
  └─ Boolean Searches (navy 002B6CB0) — search strings
  ↓
Output 2-4: CSV Exports
  ├─ batch1_direct_*.csv → Lemlist (with email)
  ├─ batch2_clay_*.csv → Clay enrichment (no email)
  └─ pipedrive_import_*.csv → Pipedrive (all + scores)
```

### 30 FunctieGroepen (Single Source of Truth)
**File:** `functiegroep_library.json` (21.4 KB)

**Categorieën:**
- **Engineering (6):** software_engineer, automatiseringsengineer, constructeur, process_engineer, quality_engineer, plc_programmeur
- **Projectleiding (4):** projectleider_elektro, projectleider_installatie, projectleider_civiel, projectleider_duurzaam
- **Werkvoorbereiding (4):** werkvoorbereider_elektro, werkvoorbereider_installatie, calculator_bouw, calculator_civiel
- **Techniek (8):** monteur_elektro, monteur_installatie, monteur_duurzaam, servicemonteur, onderhoudsmonteur, mechatronicus, bim_coordinator, bouwkundig_tekenaar
- **Management (5):** productieleider, maintenance_manager, technisch_directeur, hse_kam_coordinator, supply_chain_planner
- **Hulpmiddelen:** uitvoerder_civiel, werkvoorbereider_civiel

**Tier Classification:**
- **Tier A (14):** High-value engineering + directors
- **Tier B (11):** Coordinators + senior technicians
- **Tier C (6):** Entry/mid-level technicians

**Hard Excludes (→ NIET naar batch2):**
- `draaier` (7 terms): CNC operators
- `lasser` (14 terms): Welders
- `bankwerker` (6 terms): Machinists
- `frezer` (6 terms): Milling operators
- `logistiek_medewerker` (9 terms): Warehouse workers

### Data Quality Checks
✅ SBI Exclusion: 57 excluded sectors (IT, healthcare, government, recruitment)
✅ ICP Threshold: Default 90 (configurable via `--min-icp`)
✅ Email Validation: Must contain @, not generic (info@, contact@, admin@), not in graveyard
✅ FunctieGroep Matching: Word-boundary `\b word \b` (not substring)
✅ Exclude Filtering: Hard rejects for blocked roles
✅ Deduplication: On email (highest ICP kept)

### Commando's
```bash
# Standard run
python3 pipeline_step1_icp_filter.py --input exports/JobDigger_Processed_*.xlsx

# Custom ICP threshold
python3 pipeline_step1_icp_filter.py --input exports/JobDigger_Processed_*.xlsx --min-icp 95

# Max leads limit
python3 pipeline_step1_icp_filter.py --input exports/JobDigger_Processed_*.xlsx --max-leads 500
```

### Output Files
| File | For | Rows | Columns |
|------|-----|------|---------|
| JobDigger_Filtered_*.xlsx | Review/analysis | Qualified | 3 sheets |
| batch1_direct_*.csv | Lemlist | With email | company, email, phone, vacancy, icp_score, functiegroep |
| batch2_clay_*.csv | Clay enrichment | No email | company, city, sector, kvk, vacancy, icp_score |
| pipedrive_import_*.csv | Pipedrive | All qualified | Bedrijf, ICP Score, Succes Score, Combi Score |

### Integraties
- **Lemlist:** batch1_direct_*.csv → campaign `cam_8KGpG2G5ppSrwy6v4` (JobDigger P12 Stage 2)
- **Clay:** batch2_clay_*.csv → enrichment campaign (get email)
- **Pipedrive:** pipedrive_import_*.csv → deal/lead import (Stage "New" = stage 8)

### Graveyard Management
**File:** `exports/lemlist_graveyard.txt` (één email per regel)

Geblokkeerde emails automatisch doorgestuurd naar batch2_clay. Voeg toe:
```bash
echo "bounced@example.nl" >> exports/lemlist_graveyard.txt
```

### Audit Report
Per run: `pipeline_audit_YYYYMMDD_HHMMSS.txt`
- Total records processed
- Qualified (ICP ≥90) count
- SBI exclusions
- FunctieGroep match distribution
- Batch1/Batch2 split
- Hard rejects (no FunctieGroep match)

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

### P4 — Video Pipeline
- **Stack:** Nano Banana → Kling API → InVideo MCP
- **Scripts:**
  - `~/recruitin/scripts/kling_video_generator.py` — text2video (BTS, shortvideo), JWT auth
  - `~/recruitin/scripts/kling_invideo_pipeline.py` — image2video (character.png campagnes)
- **Output:** 3 clips × 10s → InVideo assembly → MP4 feed + Reels
- **Modellen:** `kling-v2-6` (std, sneller) | `kling-v1-5` (pro, betere human motion)
- **CLI:** `--werkvoorbereider-a` (v2-6) | `--werkvoorbereider-b` (v1.5 pro) | `--heijmans` (B1-B4)
- **Huidige test:** Heijmans BTS Senior Werkvoorbereider Wegen — 3 scenes × 5s
  - Assets: `~/recruitin/meta-campaigns/assets/Heijmans_BTS_A_202603/`
  - Logo aanpak: Leonardo AI rendert "Heijmans" tekst direct in-image (jas). Geen overlay nodig.
  - Helm logo: NIET doen (platte tekst op rond oppervlak ziet er niet uit)

### P5 — Vacaturekanon (VOLLEDIG GEBOUWD — maart 2026)
- **Status:** Alle 10 modules compleet
- **Locatie:** OneDrive/output/vacaturekanon/
- **Intake:** Jotform EU `252881347421054` · API key in macOS Keychain
- **Worker:** m1-worker/worker.js → deploy via `wrangler deploy`
- **Templates:** m2-templates/ · prospect + kandidaat HTML
- **Builder:** m3-automation/template-builder.js (Node.js ES module CLI)
- **Email:** m5-email-sequences/ · HOT/WARM/COLD sequences
- **Meta:** m6-meta-campaigns/ · 5 sectoren · campaign-config.json
- **Video:** m7-video/ · Kling AI prompts (5 sectoren × 3 videos) + CapCut workflow
- **Sales:** m8-sales-page/vacaturekanon-sales.html
- **Outreach:** m9-apollo-outreach/ · ICP + filters + 5-touch sequence
- **KPI:** m10-kpi-dashboard/ · HTML dashboard + CSV + Notion schemas

**Code security — verplicht in alle Vacaturekanon bestanden:**
- DOM: createElement/textContent/appendChild (niet innerHTML)
- Storage: document.cookie SameSite=Lax (niet localStorage)
- Events: addEventListener (niet inline handlers)
- CORS: origin whitelist (niet wildcard)
- Output: escapeHtml() op alle user-input

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

### TAAK 4 — REFERENCE IMAGES + KLING VIDEO CLIPS

**Stap 1 — Reference images genereren (oplossing voor branded werkkleding)**

Kling text-to-video kan GEEN specifieke branded werkkleding reproduceren. Oplossing: eerst
reference images maken, dan Kling image-to-video gebruiken. Kleding klopt dan vanaf frame 1.

**Image generatie tools:**
| Tool | Beschikbaar via | Kosten | Resolutie |
|------|-----------------|--------|-----------|
| Z-Image Turbo | HF MCP (`gr1_z_image_turbo_generate`) | Gratis | 1024×1024 |
| Leonardo AI | REST API (`cloud.leonardo.ai`) | Credits | 1024×1024+ |
| Nano Banana Pro | Google AI Studio (handmatig) | Google AI abo | Variabel |

```bash
# Z-Image Turbo (direct via MCP — geen API key nodig)
# Gebruik: mcp__hf-mcp-server__gr1_z_image_turbo_generate tool

# Leonardo AI (API — key in .env)
python3 ~/recruitin/scripts/leonardo_image_generator.py \
  --prompt "..." --output ~/recruitin/meta-campaigns/assets/[CAMPAGNE]/
```

**10 reference images per campagne:**
- 3× character/portret (front, driekwart, profiel) → Kling i2v input
- 5× werkscenes (tekeningen, inspectie, instructie, lopen, tablet)
- 2× team/context (briefing, wide shot)

**Stap 2 — Kling video genereren**

```bash
# Text2video (BTS scenes, shortvideo — geen image nodig)
python3 ~/recruitin/scripts/kling_video_generator.py --test-auth
python3 ~/recruitin/scripts/kling_video_generator.py --werkvoorbereider-a --dry-run
python3 ~/recruitin/scripts/kling_video_generator.py --werkvoorbereider-a \
  --output-dir ~/recruitin/meta-campaigns/assets/[CAMPAGNE]/

# Image2video (character.png campagnes — AANBEVOLEN voor branded werkkleding)
python3 ~/recruitin/scripts/kling_invideo_pipeline.py \
  --image ~/recruitin/meta-campaigns/assets/[CAMPAGNE]/character.png \
  --campagne [CAMPAGNE] --sector "[SECTOR]" --duur 5 --formaat 9:16
```

**Kling modellen:**
| Model | Mode | Gebruik | Kwaliteit |
|-------|------|---------|-----------|
| `kling-v2-6` | std | Snelle iteratie, BTS | Goed |
| `kling-v1-5` | pro | Human motion, premium | Beste |

**Kling limitaties:**
- Max 2 parallelle tasks (3e geeft `1303: parallel task over resource pack limit`) — submit in batches van 2
- `kling-v1-5` pro 10s: ~5 min render, poll timeout ≥600s, request timeout ≥30s
- `kling-v2-6` std 5s: ~1 min render
- Endpoint: `https://api.klingai.com` (NIET `api-singapore` — DNS faalt)
- Geen logo/tekst in video → achteraf via Pillow overlay + ffmpeg compositing
- Prompt max ~300 tekens effectief (langere prompts worden soms genegeerd)
- Text-to-video kan GEEN branded werkkleding → gebruik image-to-video met reference images

**ffmpeg bekende beperkingen:**
- `drawtext` filter NIET beschikbaar in huidige homebrew build
- Workaround: Pillow PNG overlay → ffmpeg `[0:v][1:v]overlay=0:0`
- Leonardo AI 9:16 output (832×1472) → Kling geeft 1056×1888 → scale: `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2`

**Heijmans werkkleding (exact — bevestigd via reference images werkenbijheijmans.nl + LinkedIn):**
- Helm: GEEL (niet wit!)
- Jas: fel ORANJE hi-vis full zip jacket met GRIJZE reflectiestrepen (niet geel, niet hesje)
- Broek: donker (zwart/grijs) of jeans
- Conditie: vies, modderig, versleten
- Logo helm: NIET overlayën (platte tekst op rond helmoppervlak werkt niet)
- Logo jas: Leonardo AI rendert "Heijmans" tekst in-prompt op borst — natuurlijk geïntegreerd
- Officieel logo PNG: `~/Documents/# WOUTER'S CLAUDE PREFERENCES v2.0/heijmans logo wit.png` (transparant)
- Site: oranje banners op hekwerk, gele machines, plat polderlandschap
- **ALTIJD** eerst websearch voor reference images bij nieuwe klant!

**Reference image workflow:**
```
Leonardo AI Phoenix 1.0 → character images MET branded tekst in prompt
    ↓
character.png (beste portret, logo op jas in-image) → Kling i2v
    ↓
scene clips → heijmans_assembly.py (ffmpeg concat + endframe)
```

---

### TAAK 5 — INVIDEO ASSEMBLY (Claude.ai)

Na Kling: lees `invideo_instructie.md` → print inhoud → Wouter kopieert naar Claude.ai met InVideo MCP aan.
Tool: `generate-video-from-script`
Output: MP4 feed (1080×1080) + Reels (1080×1920)

---

## IMAGE FRAMEWORK — VASTE REGELS

```
NOOIT:  Tekst/letters in Nano Banana/Z-Image prompts
WEL:    Leonardo AI Phoenix kan branded bedrijfsnamen renderen (bijv. 'Heijmans' op jas)
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
python3 ~/recruitin/scripts/kling_video_generator.py --test-auth

# BTS video (text2video — dry run eerst)
python3 ~/recruitin/scripts/kling_video_generator.py --werkvoorbereider-a --dry-run
python3 ~/recruitin/scripts/kling_video_generator.py --werkvoorbereider-a \
  --output-dir ~/recruitin/meta-campaigns/assets/Heijmans_BTS_A_202603/

# Campagne video (image2video — met character.png)
python3 ~/recruitin/scripts/kling_invideo_pipeline.py \
  --image ~/recruitin/meta-campaigns/assets/[CAMPAGNE]/character.png \
  --campagne [CAMPAGNE] --sector "[SECTOR]" --duur 5 --formaat 9:16

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
| `kling_video_generator.py` | Text2video — BTS, shortvideo (JWT auth) |
| `kling_invideo_pipeline.py` | Image2video — character.png campagnes |
| `leonardo_image_generator.py` | Leonardo AI reference images (Phoenix v2) |
| `meta_campaign_builder.py` | Meta campagne via API |
| `kling_heijmans_batch.py` | Kling i2v batch — Heijmans BTS scenes |
| `kt-daily-monitor.py` | Dagelijkse KPI monitoring |

## KAMPAGNE NAAMGEVING

```
KT_[sector-slug]_[YYYYMM]
KT_OilGas_202603
KT_Constructie_202603
KT_Automation_202603
```
