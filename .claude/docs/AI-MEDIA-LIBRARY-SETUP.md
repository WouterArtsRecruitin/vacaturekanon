# RECRUITIN AI MEDIA LIBRARY
# Google Drive — Centrale asset opslag voor alle AI tools
# Antigravity leest alles via Google Drive MCP
# Laatste update: 2026-03-04

---

## GOOGLE DRIVE MAPSTRUCTUUR

Maak aan op: `Mijn Drive / Recruitin / AI-Media-Library /`

```
📁 AI-Media-Library/
│
├── 📁 00_CHARACTERS/
│   ├── 📁 karakter-A-man-40-blauw-werkpak/
│   │   ├── character-seed.png          ← DNA referentie image
│   │   ├── character-dna.md            ← Prompt tekst (exact)
│   │   ├── visual-1-probleem.png
│   │   ├── visual-2-autoriteit.png
│   │   ├── visual-3-sociaal.png
│   │   └── visual-4-cta.png
│   ├── 📁 karakter-B-vrouw-35-zakelijk/
│   └── 📁 karakter-C-team-divers/
│
├── 📁 01_IMAGES/
│   ├── 📁 nano-banana/
│   │   ├── 📁 KT_OilGas_202603/
│   │   │   ├── visual-1.png
│   │   │   ├── visual-2.png
│   │   │   ├── visual-3.png
│   │   │   └── visual-4.png
│   │   ├── 📁 KT_Constructie_202603/
│   │   └── 📁 KT_Automation_202603/
│   │
│   ├── 📁 leonardo/
│   │   ├── 📁 KT_OilGas_202603/
│   │   │   ├── leonardo-v1-realistic.png
│   │   │   ├── leonardo-v2-cinematic.png
│   │   │   └── leonardo-v3-editorial.png
│   │   └── 📁 KT_Constructie_202603/
│   │
│   └── 📁 gemini-flow/
│       ├── 📁 KT_OilGas_202603/
│       └── 📁 stills/
│
├── 📁 02_VIDEOS/
│   ├── 📁 kling/
│   │   ├── 📁 KT_OilGas_202603/
│   │   │   ├── scene_01_probleem.mp4
│   │   │   ├── scene_02_inzicht.mp4
│   │   │   └── scene_03_cta.mp4
│   │   └── 📁 KT_Constructie_202603/
│   │
│   ├── 📁 invideo/
│   │   ├── 📁 KT_OilGas_202603/
│   │   │   ├── KT_OilGas_feed_1080x1080.mp4
│   │   │   └── KT_OilGas_reels_1080x1920.mp4
│   │   └── 📁 KT_Constructie_202603/
│   │
│   └── 📁 flow-veo/
│       ├── 📁 KT_OilGas_202603/
│       └── 📁 raw-clips/
│
├── 📁 03_CAMPAGNES/
│   ├── 📁 KT_OilGas_202603/
│   │   ├── campaign-ids.json
│   │   ├── campaign-input.md
│   │   ├── ad-copy.json
│   │   ├── landing-page-url.txt
│   │   └── rapport.json
│   └── 📁 KT_Constructie_202603/
│
├── 📁 04_PROMPTS/
│   ├── character-dna-templates.md     ← Alle DNA prompts per karakter
│   ├── scene-prompts-library.md       ← Bewezen werkende scene prompts
│   ├── invideo-scripts.md             ← InVideo scripts per sector
│   └── negative-prompts.md           ← Vaste negatieve prompts
│
└── 📁 05_ARCHIVE/
    └── 📁 [JJJJMM]/                  ← Maandelijks archief
```

---

## NAAMGEVING REGELS (altijd consistent)

```
Images:    [karakter]-[emotie]-[tool]-[versie].png
           bijv: man40-probleem-nano-v1.png

Videos:    [campagne]-[scene]-[tool]-[formaat].mp4
           bijv: KT_OilGas-scene01-kling-1x1.mp4

Campagne:  KT_[sector]_[YYYYMM]
           bijv: KT_OilGas_202603

Karakter:  karakter-[geslacht][leeftijd]-[beschrijving]
           bijv: karakter-man40-blauw-werkpak
```

---

## ZAPIER AUTOMATIONS — automatisch uploaden per tool

### Automation 1 — Kling clips → Drive

```
Trigger:  Webhook (Kling pipeline script stuurt dit)
  Body:   { "file_path": "...", "campagne": "...", "scene": "..." }

Action 1: Google Drive → Upload File
  Folder: AI-Media-Library/02_VIDEOS/kling/[campagne]/
  Naam:   [campagne]-scene_[scene]-kling-1x1.mp4

Action 2: Google Sheets → Add Row (Asset Register)
  Sheet:  AI-Media-Library/asset-register.gsheet
  Data:   datum, tool, campagne, bestandsnaam, drive-url, type
```

Voeg dit toe aan `kling_invideo_pipeline.py`:
```python
def upload_to_drive_via_zapier(file_path, campagne, scene_nr, tool="kling"):
    """Upload clip naar Google Drive via Zapier webhook"""
    webhook_url = os.getenv("ZAPIER_DRIVE_WEBHOOK")
    if not webhook_url:
        return

    with open(file_path, "rb") as f:
        file_data = base64.b64encode(f.read()).decode()

    payload = {
        "file_path":  file_path,
        "file_data":  file_data,
        "campagne":   campagne,
        "scene":      f"scene_{scene_nr:02d}",
        "tool":       tool,
        "timestamp":  datetime.now().isoformat(),
    }
    try:
        r = requests.post(webhook_url, json=payload, timeout=30)
        print(f"  ✓ Drive upload: scene_{scene_nr} → {r.status_code}")
    except Exception as e:
        print(f"  ⚠ Drive upload mislukt: {e}")
```

### Automation 2 — InVideo output → Drive

```
Trigger:  InVideo webhook (na video export)
  OF:     Handmatig via Zapier "Push" knop

Action:   Google Drive → Upload File
  Folder: AI-Media-Library/02_VIDEOS/invideo/[campagne]/
```

### Automation 3 — Leonardo images → Drive

```
Trigger:  Leonardo AI webhook (na image generatie)
  URL:    Settings → Webhooks → Add webhook

Action 1: Webhooks → GET (download image van Leonardo URL)
Action 2: Google Drive → Upload File
  Folder: AI-Media-Library/01_IMAGES/leonardo/[campagne]/
  Naam:   [campagne]-[stijl]-leonardo-v[n].png

Action 3: Google Sheets → Asset Register bijwerken
```

### Automation 4 — Flow/Gemini → Drive

```
Trigger:  Gmail → New Email (van noreply@google.com met "Flow export")
  OF:     Handmatig downloaden + Zapier Push

Action:   Google Drive → Upload File
  Folder: AI-Media-Library/02_VIDEOS/flow-veo/[campagne]/
```

---

## ASSET REGISTER — Google Sheets

Maak aan: `AI-Media-Library/asset-register.gsheet`

| Datum | Tool | Campagne | Bestandsnaam | Type | Drive URL | Formaat | Status | Gebruikt in Meta |
|-------|------|----------|--------------|------|-----------|---------|--------|-----------------|
| 2026-03-04 | nano-banana | KT_OilGas_202603 | visual-1.png | image | [url] | 1080x1080 | approved | ja |
| 2026-03-04 | kling | KT_OilGas_202603 | scene_01.mp4 | video | [url] | 1:1 | raw | nee |
| 2026-03-04 | leonardo | KT_OilGas_202603 | leonardo-v1.png | image | [url] | 1080x1080 | review | nee |

Antigravity kan dit sheet lezen via Google Drive MCP en weet dan direct:
- Welke assets beschikbaar zijn per campagne
- Welke al gebruikt zijn in Meta
- Welke nog goedkeuring nodig hebben

---

## ANTIGRAVITY INTEGRATIE — GEMINI.md

Sla op als: `~/.gemini/antigravity/GEMINI.md`

```markdown
# RECRUITIN B.V. — Antigravity Configuratie
# Wouter Arts | DGA

## GOOGLE DRIVE MEDIA LIBRARY

Alle AI-gegenereerde assets staan in Google Drive:
Pad: Mijn Drive / Recruitin / AI-Media-Library /

Via Google Drive MCP kun je:
- Assets ophalen per campagne
- Nieuwe files uploaden na generatie
- Asset Register lezen (asset-register.gsheet)

## TOOLS EN BRONNEN

| Tool | Drive map | Bestandstype |
|------|-----------|-------------|
| Nano Banana | 01_IMAGES/nano-banana/ | .png |
| Leonardo | 01_IMAGES/leonardo/ | .png |
| Gemini/Flow | 01_IMAGES/gemini-flow/ | .png |
| Kling | 02_VIDEOS/kling/ | .mp4 |
| InVideo | 02_VIDEOS/invideo/ | .mp4 |
| Flow/Veo | 02_VIDEOS/flow-veo/ | .mp4 |

## WERKWIJZE BIJ CAMPAGNE TAKEN

1. Lees ~/recruitin/.claude/CLAUDE.md
2. Check Drive MCP: welke assets bestaan al voor deze campagne?
3. Genereer ontbrekende assets (geen duplicaten!)
4. Upload naar juiste Drive map na generatie
5. Update asset-register.gsheet

## CHARACTER DNA LOCATIE

Altijd ophalen via Drive MCP:
AI-Media-Library/00_CHARACTERS/[karakter]/character-dna.md

Nooit uit geheugen — altijd uit Drive lezen.

## SECTOR MAPPING

oil & gas       → KT_OilGas_[YYYYMM]
constructie     → KT_Constructie_[YYYYMM]
automation      → KT_Automation_[YYYYMM]
productie       → KT_Productie_[YYYYMM]
renewable       → KT_Renewable_[YYYYMM]
```

---

## ANTIGRAVITY AGENT PROMPT — Library raadplegen

Gebruik dit in Agent Manager als je assets wilt ophalen:

```
Gebruik Google Drive MCP.

Zoek in: AI-Media-Library/01_IMAGES/nano-banana/[CAMPAGNE]/
en:      AI-Media-Library/02_VIDEOS/kling/[CAMPAGNE]/

Geef een overzicht van alle beschikbare assets voor campagne [NAAM].
Lees ook asset-register.gsheet en geef aan welke nog niet gebruikt zijn in Meta.
```

---

## EENMALIGE SETUP — Stap voor stap

**Stap 1 — Google Drive mappen aanmaken**
```
Ga naar drive.google.com
Maak de volledige mapstructuur hierboven aan
(Of: vraag Antigravity dit via Drive MCP te doen)
```

**Stap 2 — Asset Register aanmaken**
```
Maak nieuw Google Sheet aan in AI-Media-Library/
Naam: asset-register
Kolommen: datum | tool | campagne | bestandsnaam | type | drive_url | formaat | status | meta
```

**Stap 3 — Zapier webhooks instellen**
```
zapier.com → Create Zap → Webhooks trigger
Kopieer webhook URL → sla op in .env:
ZAPIER_DRIVE_WEBHOOK=https://hooks.zapier.com/hooks/catch/[ID]/[KEY]/
```

**Stap 4 — Leonardo webhook instellen**
```
app.leonardo.ai → Settings → Webhooks
Add: [jouw Zapier webhook URL voor Leonardo]
```

**Stap 5 — Antigravity Drive MCP activeren**
```
Antigravity → Agent session → ... → MCP Servers
Zoek: Google Drive
Activeer → Log in met Google account
```

**Stap 6 — GEMINI.md opslaan**
```bash
mkdir -p ~/.gemini/antigravity
nano ~/.gemini/antigravity/GEMINI.md
# Plak de inhoud uit sectie hierboven
```

**Stap 7 — Bestaande assets uploaden**
```
Sleep handmatig alle bestaande Kling/Leonardo/Nano Banana
assets naar de juiste Drive mappen
```

---

## RESULTAAT NA SETUP

```
Jij genereert image in Nano Banana (Gemini)
    ↓ (handmatig of auto via Gemini export)
Google Drive: AI-Media-Library/01_IMAGES/nano-banana/[campagne]/

Jij genereert video in Leonardo
    ↓ (Leonardo webhook → Zapier)
Google Drive: AI-Media-Library/01_IMAGES/leonardo/[campagne]/

Kling pipeline draait
    ↓ (script → Zapier webhook)
Google Drive: AI-Media-Library/02_VIDEOS/kling/[campagne]/

InVideo export klaar
    ↓ (handmatig of InVideo webhook)
Google Drive: AI-Media-Library/02_VIDEOS/invideo/[campagne]/

Flow/Veo export
    ↓ (handmatig download → Drive)
Google Drive: AI-Media-Library/02_VIDEOS/flow-veo/[campagne]/

════════════════════════════════════
Antigravity leest alles via Drive MCP
Claude.ai leest alles via Drive MCP
Asset Register bijgehouden in Sheets
════════════════════════════════════
```
