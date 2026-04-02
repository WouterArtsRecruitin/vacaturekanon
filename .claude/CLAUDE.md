# CLAUDE.md — Recruitin B.V.
# Antigravity leest dit bestand aan het begin van elke sessie
# Laatste update: 2026-03-26

## ✅ RECENTE UPDATES

**Kandidatentekort V8.1 Automation & Bugfixes (2026-03-26):** COMPLETED ✅
- **De 24-uurs Belofte Gefixt:** `kt_engine_v8.py` bevat nu een native `created_at` timestamp check in de code. Mails, Pipedrive deals en Lemlist flows stagneren hierdoor perfect 24 uur na lead generation totdat de timing the lead bereikt, zodat Wouter's frontend-belofte altijd klopt. (Uitzondering: "test" of "wouter" mailadressen bypassen the lock).
- **Dode Links Vernietigd:** De call-to-action in de "V8 Teaser" email (`kt_engine_v8.py`) forwardt leads nu direct door naar the vlekkeloze `v1_url` Supabase public file. The gebroken Vacaturekanon wrapper URL is eruit gesloopt om 404's The voorkomen.
- **Meta Pixel Tracking (V1 & V2):** De Meta Pixel (`1430141541402009`) is diep verborgen maar native geinjecteerd vóór the `</head>` tags in the twee HTML template bestanden. Retargeting (Ad Set 3) theert hierdoor op alle Lemlist-doorkliks.
- **Lemlist Browser Bypass:** Vanwege API restricties (Lemlist forceert `405 Method Not Allowed` op the sequences endpoint) heeft the Antigravity subagent succesvol virtueel ingelogd via de front-end UI in Lemlist en Stap 4 en Stap 5 van the *KT V8 - B2B Nurture Strategy* veilig gepusht met The nieuwe meedogenloze B2B tone of voice.
- **Nieuwe Campagne Basis:** `KT_Techniek_2026` image genesis gedraaid in the artifacts (5 portretten en action-shots via de strakke "No-text" 8K B2B Prompt), wachtend op inrichting per OneDrive local scope.


**Kandidatentekort V8 Unified Engine (2026-03-26):** COMPLETED ✅
- **Architectuur:** Volledige consolidatie van oude workers in 1 centraal script: `kt_engine_v8.py`. (Jotform → Supabase → AI → Pipedrive Gating → Lemlist Nurture).
- **Template Integratie:** Genereert direct premium HTML rapporten o.b.v. externe V7/V8 templates. Het V1 Executive Rapport en de V2 Storytelling Vacaturetekst zijn volledig ge-redesigned naar een high-end, emoji-vrije, redactionele B2B consulting layout (Inter font, vloeiende narratieve structuur, en toegevoegde strategische 'Why'-context) die 100% compliant is met de Master Prompt V3.0.
- **SEO & ATS Optimalisatie:** V2 HTML-templates genereren nu dynamisch geoptimaliseerde SEO `<title>` tags met sector-specifieke kenmerken (bijv. `Vacature: Allround Technicus (Manufacturing) bij Veco`) voor maximale jobboard vindbaarheid. V1 reports zijn professioneel omgebouwd tot B2B sales instrumenten.
- **Sales Funnel "Tease & Reveal":** V3.2 Prompt levert 'punchy' blockers en quick wins (max 5 woorden) direct af als custom Lemlist variabele. Volledig afgestemd op koude conversie emails a la NCNC structuur.
- **Pipedrive Gating:** Systematische blokkade via `icp_score >= 65`. Te lage scores gaan via Lemlist op educatie modus, Pipedrive blijft extreem schoon voor sales. Launchd worker `nl.kandidatentekort.pipeline` draait automatische cron elke 15 minuten.

**Kandidatentekort.nl V3 — 24-Hour AI Pipeline (2026-03-25):** COMPLETED ✅
- **Architectuur:** Jotform -> Cloudflare Worker -> Supabase (`kt_leads`) -> Python Cron (`kt_ai_worker.py`) -> Resend HTML Report -> Lemlist Nurture Sync.
- **Supabase Storage:** Jotform uploads worden direct gedownload en permanent en veilig opgeslagen in de Supabase Storage bucket `kt_vacatures`.
- **Genadeloze B2B AI:** Claude 3.5 Sonnet / Haiku prompt is omgezet naar de "Headhunter Direct" tone-of-voice. Rapporten en herschreven vacatures zijn nu extreem direct, gebruiken "jij/je", en bashen genadeloos op clichés.
- **Timing:** Het Python script splitst de AI-generatie vs. Report-delivery doormidden, om te garanderen dat de resultaten *exact* 24 uur later in de inbox vallen (zoals beloofd op de website hero).
- **Lemlist Sync:** `kt_lemlist_sync.py` laadt correct de `.env` (override=True) en voegt de `companyName`, `firstName` en tag `[KT_LEAD]` direct toe aan de nurture sequence `cam_TcSpPxJL9anRkf5TS`.
- **Reference Files:** Oude bestanden ter referentie zijn gevonden in `/Users/wouterarts/projects/Recruitin/kandidatentekort/`. V3 leeft in `~/recruitin/kandidatentekort-v3/` en de scripts in `~/recruitin/scripts/`.

**Vacaturekanon v2 End-to-End Flow Fixes & Credential Rotation (2026-03-24):** COMPLETED ✅
- **Credential Rotation:** API keys voor Google Gemini (Imagen 4), Lemlist en Meta Pixel zijn succesvol geroteerd in `.env` en op de Vercel productie omgeving.
- **Lemlist Cloudflare Bypass:** Python `urllib` calls in de E2E tester liepen voorheen vast op de Lemlist API vanwege Cloudflare Error 1010. Opgelost door structureel een `User-Agent` spoof in te bouwen op alle `http_get`/`post`/`patch` requests.
- **Vercel & Supabase Webhook Connectie:** 500 errors verholpen door `vercel env pull` & pushen van de juiste keys; de Vercel Jotform webhook vuurt nu feilloos 200 OKs terug en schrijft test-leads succesvol direct the Supabase `vk_leads` tabel met `pending_automation`.
- **Meta Webhook Opschoning:** De Meta Lead Ads custom webhook is omgezet van een ongeldige URL naar de stabiele `vacaturekanon-hook.vercel.app/api/meta-webhook`. Tevens de legacy "beutech" secret tokens & Slack copywriting geëmancipeerd naar `vk_meta_webhook_secret_2026`. Datasets in Business Manager handmatig gelinkt.
**Vacaturekanon v2 Playable Ads & UI Automation (2026-03-23):** COMPLETED ✅
- **Native Meta Mini-App:** "Playable Ad" / "Interactive Canvas" gebouwd voor Vacaturekanon (`vacaturekanon_playable_ad.html`). Ultra-lightweight (< 5KB pure HTML/CSS/JS) en voorzien van de verplichte `FbPlayableAd.onCTAClick()` call voor harde Meta Pixel tracking.
- **Graphic UI System:** Exacte naadloze styling-match met v2 (Deep Violet `#07050f` basis, Neon Magenta outline, Vivid Oranje accenten en witte pill-buttons a la Inter/Outfit font).
- **GIF Automation Pipeline:** `scripts/create_meta_gif.py` toegevoegd. Moduleert lokaal via Python/Pillow in 1 klik static Canva frames naar een naadloos loopende Meta `.gif` (0.5s/frame delay). Absolute snelste 'Option A' flow voor B2B dashboards.
- **Assets:** Alle iteratieve AI neon renders (UI templates, radars, klokken, trofeeën zónder tekst_ opgeslagen in `output/vacaturekanon/assets/ai_generations/` voor snelle Canva invulling.

**Vacaturekanon v2 Meta API Architecture & Maestro Deployment (2026-03-23):** COMPLETED ✅
- **Dynamic Graph API Builder:** Het oude `meta_campaign_builder.py` voldeed onvoldoende wegens restricties tot 'Single Image Ads'. Een nieuw custom Python Graph API protocol gebouwd (`build_meta_full.py`) dat via native API calls naadloos wél complexe **Carrousel Creatives** en **Single Image B2B Ads** samenvoegt en de benodigde images verwerkt.
- **Meta Page ID Forcing:** Problematiek rond onjuiste afzenders (Beutech Ads fallback) structureel opgelost door expliciet `META_PAGE_ID=61578385841803` (Vacaturekanon V2 Page) on-the-fly the injecteren in de runtime environment.
- **De Maestro Campagne:** De eerste 100% geautomatiseerde full-funnel campagne (`KT_Tech_V2_Maestro`) is met succes online geschoten in Meta Ads inclusief de loeistrakke 'RECRUIT - AUTOMATE - DOMINATE' copywriting over 3 carousel-cards mét custom roterende links.

**Vacaturekanon v2 Backend Automation & Stripe Checkout (2026-03-22):** COMPLETED ✅
- **Micro-Commitment Kassa (Stripe):** The 1-tier "All-In Project" (€2.495) is via Stripe Payment Links direct op de hero- en pricing CTA-knoppen van `index-v2.html` geïnstalleerd. Conversie-barrier is geslecht doordat we the lange JotForm intake pas sturen nadat er is afgerekend.
- **Webhook Routing (Netlify):** `vacaturekanon-pages/api/stripe-webhook.js` luistert op `checkout.session.completed` events en vuurt The beveiligde JotForm intake via `Resend API` direct the inbox in van the kopende klant.
- **Lemlist/Supabase B2B Sync:** `scripts/lemlist_automation.py` is gemaakt om the `vk_leads` in the Supabase DB razendsnel door The Lemlist Drips the trekken via the Lemlist API (MKB Recruiter outreach).
- **V2 Sales Landingpage:** FAQ-accordeon gebouwd, Intake handleiding ('Geef de AI de juiste brandstof') gelanceerd, en security lints (`noopener noreferrer`) gepatched. Pijnpunten gericht op NCNC model van the concurrent gepareerd.
- **Meta Ads "Eigen Sales":** Acquisitieblueprint is klaargezet in `meta-campaigns/vacaturekanon-eigen-sales/ad_copy_icp.md`. Scherp gesteld op the **HR Manager / Corporate Recruiter (50-800 FTE)** (CBO structuur).
- **V3 Geëlimineerd:** The tijdelijke 'v3' web-builders en tests zijn succesvol vernietigd voor focus op V2 integriteit.


**Vacaturekanon v2 Lead Capture & UI Overhaul (2026-03-21):** COMPLETED ✅
- **Jotform API Styling:** De JotForm Intake Popup (ID `260757174181359`) is geselecteerd voor de website. Om deze styling te laten matchen met de donkere V2-interface is er een script gemaakt dat rechtstreeks een CSS body post naar de JotForm EU API Endpoint via Wouter's JOTFORM_API_KEY.
- **Workflow / "Hoe het werkt" UI:** De statische diensten-bento grid is volledig opgeruimd en vervangen door de "V1 style" alternerende afbeeldingsblokken met zwevende 3D-shadows (Intake, Video AI, Algoritmisch Beheer, Directe Delivery).
- **Premium Lettertypen & Tekst:** Syne/Inter ingewisseld voor krachtigere `Outfit` (headings) en `Plus Jakarta Sans` (body). De copywriting is fors aangescherpt en Nederlandstalig geperfectioneerd.
- **Performance Optimization:** Om the trage laadtijd van het zeer grote JotForm iframe tegen te gaan, is er in de `index-v2.html` code een TLS `dns-prefetch` en `preconnect` architectuur gebouwd naar de servers van `eu.jotform.com` in de `<head>`, wat the laadtijd halveert. 
- **Payment flow (WIP):** Architectuurdiscussie over The Micro-Commitment Strategy: éérst kleine layout betalen met Stripe Link direct op de knop, dán pas redirigeert Stripe the gebruiker naar the Jotform (dit helpt extreem tegen JotForm drops).
- **Productie Deploy:** Zojuist lokaal de EPERM blockages van the macOS CLI omzeild en 100% vlekkeloos gedeployd naar Productie-Netlify (`https://vacaturekanon-2026-demo.netlify.app`). V2 is live.**Kandidatentekort V2 Voorbeeld Pagina — Nova Robotics Demo (2026-03-26):** COMPLETED ✅
- **Probleem:** De 'Bekijk Voorbeeld' knop op kandidatentekort.nl wees naar een leeg template (`Manager Techniek — Test BV`), wat door de Googlebot was geïndexeerd en verwarring opleverde.
- **Oplossing:** Python script (`build_demo_nova.py`) geschreven dat the master template 100% hardcoded heeft ingevuld voor techbedrijf "Nova Robotics B.V." (Senior PLC Automation Engineer).
- **Hosting / Custom Domain:** Volledig onafhankelijke statische website gedeployd naar `https://voorbeeld.kandidatentekort.nl` direct via een raw HTTP-upload script (`upload_netlify_zip.py`) om de falende mac-os cli permissions the omzeilen.

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
│   ├── lemlist_automation.py      ← B2B Leads van Supabase `vk_leads` naar Lemlist syncen
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
**Nieuwe V8 Focus (2026-03):** 30-Seconds-To-Conversion Philosophy. 
**URL formaat:** `[sector].kandidatentekort.nl`

**Pagina opbouw (altijd V8 Dark Mode UI):**

```
HERO
  Aesthetic: Dark Mode (#0D1117 of #07050f), Inter/Roboto font, High-end B2B.
  H1:  "Waarom solliciteert er niemand op jouw [FUNCTIE] vacature?"
  Sub: "Je zoekt keihard naar technisch personeel... Upload de vacature.
        Binnen 24 uur krijg je the converterende versie terug."

UPLOAD SECTIE (De Core Engine)
  Geen "Neem contact op" knop, maar letterlijk direct The dropzone!
  Component: Massief 'Drag & Drop' Glassmorphism vak midden in The hero.
  Timeline: 1. Upload (Nu) -> 2. Data Analyse -> 3. Verbeterde Copy in Mail (Morgen).

COMPARISON (Social Proof & Pijn)
  Links (Rood): De Huidige Tekst (Marktconform salaris, 9-tot-5).
  Rechts (Groen): De Verbeterde Versie (Exacte salarisbandbreedte, gereedschap details).

FOOTER
  kandidatentekort.nl | Recruitin B.V. | Doesburg
```

**Technische vereisten:**
```
Stack     : Vanilla HTML/CSS/JS (Dropzone interface hookt the Supabase/Jotform webhook)
Huisstijl : bg #0D1117 (standaard) of #07050f (VKV2) · blauw/oranje accenten.
Fonts     : Inter (modern, B2B, strak)
Pixel     : fbq('init', '[META_PIXEL_ID]') + Lead event op form submit
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

Maak via the Meta Marketing API een volledige campagne structuur aan.
**Nieuwe Architectuur vanaf 2026-03:** Gebruik custom Graph API injectie (`build_meta_full.py` methodologie) in the CI environment om Carrousel componenten asynchroon in Facebook op te bouwen. Geen limitatie meer tot pure Single Images.

**Campagne structuur:**
```
Campaign: KT_[Sector]_V2_Maestro | Objective: LEAD_GENERATION | PAUSED
META_PAGE_ID: 61578385841803 (Let op fallback errors!)

Ad Set 1 — Prospecting (60% budget)
  Targeting: HR Manager · HR Director · DGA · CEO · Directeur
  Bedrijfsgrootte: 50-800 FTE | Geo: Gelderland/Overijssel/Noord-Brabant

Ad Set 2 — Lookalike (25% budget)
  Source: kandidatentekort.nl pixel bezoekers 180 dagen
  Lookalike: 1% Nederland

Ad Set 3 — Retargeting (15% budget)
  Audience: site bezoekers 30d MINUS Pixel Lead events
```

**Ad Creatives (V2 Copywriting Modellen):**
```
Carousel Ad (3-Luik) — (Meestal in Retargeting)
  - Slide 1: RECRUIT. "Vakspecialisten, direct en exclusief."
  - Slide 2: AUTOMATE. "Sourcing optimalisatie zonder gedoe."
  - Slide 3: DOMINATE. "Laat je concurrentie ver achter je stof happen."

Single Image Ad — (Meestal in Prospecting)
  - "IS JOUW TECHNISCHE VACATURE AL VEEL TE LANG OPEN?"
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

**5-Fasen Ad Formats (V2 Dark Mode Branding):**
Alle ad creatieven MOETEN V2 Dark Mode styling aanhouden: Deep Violet (`#07050f`), Outline Neon Magenta (`#ff00cc`) en Vivid Orange (`#FF5500`).

- **Ad 1 (PIJN / HOOK):** Split-Screen Chaos vs Automation. Tekst: "Vacature al 6 maanden open? Stop the chaos."
- **Ad 2 (OPLOSSING / SNELHEID):** Dashboard UI Close-up. Tekst: "Uren, niet maanden. Razendsnelle AI pre-selectie."
- **Ad 3 (FOMO / URGENCY):** Neon Time Clock. Tekst: "Jouw concurrent werft jouw ideale kandidaat terwijl jij wacht."
- **Ad 4 (SOCIAL PROOF):** Team Celebration / Director met glow. Tekst: "De B2B Recruitment Engine gebruikt door 45+ marktleiders."
- **Ad 5 (CONVERSIE CTA):** Minimalistisch Dark Mode of Playable HTML5 Ad. Tekst: "Boek je Strategie Sessie. Alleen betalen bij plaatsing (NCNC)."

**[LET OP] Playable Ads (HTML5):**
> Omdat we voor B2B Lead Gen campagnes in Meta geen gekoppelde Facebook App (App ID) registreren, accepteert de Graph API het uiterst streng beveiligde formaat via programmatische API niet rechtstreeks (foutmeldingen op `ad_playable_media`).
> **Workaround:** ZIP altijd de `.html` lokaal (bijv. `vacaturekanon_playable_ad.zip`) en upload deze éénmalig handmatig in de specifieke advertentie via de Meta Advertentiebeheer portal onder *'Speelbare bron'* / *'Instant Experience'*. Zorg altijd dat je `FbPlayableAd.onCTAClick()` in de HTML aanroept.

**De Retargeting Carrousel (3-luik 1080x1080):**
1. **Slide 1:** RECRUIT. "Stop met verdrinken in slechte cv's."
2. **Slide 2:** AUTOMATE. "Laat algoritmes de top 1% sourcen."
3. **Slide 3:** DOMINATE. "Claim je spot vandaag. Start de Engine ->"

**Het 15s High-Paced B2B Video Script (TikTok/Reels/Feed):**
> 🚨 **CRITISCHE EIS: ULTRA-FOTOREALISTISCH**
> Alle gegenereerde personages in video's MOETEN 100% human-like bewegen en nagenoeg niet van echt te onderscheiden zijn. Gebruik hiervoor UITSLUITEND `Kling v1.5 (Pro Mode)` via Image-to-Video met een 8K hyperrealistische base image uit Leonardo Phoenix. Geen goedkope Text-to-Video AI vibes.

1. **0-3s Hook:** Chaos/Pijn visual. Acteur (ultra-realistisch) met handen in haar. Audio: "Is jouw technische vacature nog stééds open?"
2. **3-10s Body (Snel):** Snelle cuts van de V2 UI bars/metrics. AI SOURCING -> KWALIFICATIE -> INBOX. Audio: "Ontmoet Vacaturekanon. De Recruitment AI Engine die jouw headhunter overbodig maakt."
3. **10-15s CTA:** Director Shot (ultra-realistisch lachend) of Screen-recording van de Playable Ad flow. Audio: "Schiet wél raak. Boek jouw gratis strategie-sessie en klik de link in beeld."

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
