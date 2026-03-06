# ANTIGRAVITY MASTER PROMPT v2
# Trigger: Jotform submit → volledige campagne automation
# Output: Dynamische landing page + Meta campagne + Kling clips (per sector)
# Recruitin B.V. | Wouter Arts

---

## ARCHITECTUUR OVERZICHT

```
kandidatentekort.nl Jotform submit
        ↓
Zapier webhook → Antigravity trigger
        ↓
┌─────────────────────────────────┐
│  ANTIGRAVITY AGENT              │
│                                 │
│  TAAK 1 — Character image       │
│  TAAK 2 — Dynamische LP bouwen  │
│  TAAK 3 — Meta campagne API     │
│  TAAK 4 — Kling video clips     │
│  TAAK 5 — Alles koppelen        │
└─────────────────────────────────┘
        ↓
Slack: "Campagne live voor [bedrijf]"
```

---

## STAP 0 — ZAPIER SETUP (eenmalig)

Maak dit Zapier workflow aan:

```
Trigger: Jotform → New Submission
  Form: kandidatentekort.nl aanvraagformulier

Filter: Alleen als sector NIET leeg is

Action 1: Formatter → extract velden
  sector    = {{sector}}
  functie   = {{functie}}
  bedrijf   = {{bedrijf_naam}}
  regio     = {{regio}}
  email     = {{email}}
  naam      = {{naam}}

Action 2: Webhooks by Zapier → POST
  URL: [jouw Antigravity webhook URL]
  Body (JSON):
  {
    "sector":   "{{sector}}",
    "functie":  "{{functie}}",
    "bedrijf":  "{{bedrijf_naam}}",
    "regio":    "{{regio}}",
    "email":    "{{email}}",
    "naam":     "{{naam}}",
    "timestamp":"{{zap_meta_human_now}}"
  }
```

Antigravity webhook URL → Settings → Integrations → Webhook URL

---

## ANTIGRAVITY AGENT PROMPT
## (plak dit als systeem prompt in Agent Manager)

```
Je bent de campagne automation agent van Recruitin B.V.
Lees altijd eerst: ~/recruitin/.claude/CLAUDE.md

Wanneer je een webhook payload ontvangt met sector, functie,
bedrijf, regio en email — voer je automatisch alle onderstaande
taken uit in volgorde. Stop niet tenzij er een fatale fout is.
Stuur bij elke voltooide taak een Slack notificatie.
```

---

## WEBHOOK PAYLOAD

```json
{
  "sector":    "oil & gas",
  "functie":   "Procesoperator",
  "bedrijf":   "Acme Refinery B.V.",
  "regio":     "Gelderland",
  "email":     "hr@acme.nl",
  "naam":      "Jan de Vries",
  "timestamp": "2026-03-04 09:00"
}
```

Uit deze data wordt alles afgeleid:
```
CAMPAGNE_NAAM = KT_[sector_slug]_[YYYYMM]
  bijv: KT_OilGas_202603

SUBDOMAIN = [sector_slug].kandidatentekort.nl
  bijv: oilgas.kandidatentekort.nl

sector_slug = sector lowercase, spaties vervangen door koppelteken
  "oil & gas" → "oil-gas"
  "constructie" → "constructie"
  "automation" → "automation"
```

---

## TAAK 1 — CHARACTER IMAGE

Genereer via Nano Banana / Imagen 4.

**Character DNA prompt:**
```
Een begin-40-jarige West-Europese man, donkerbruin haar
kort en netjes gekamt, lichtgeschoren baard, sterke kaaklijnen,
donkerblauw werkpak, zelfverzekerd maar benaderbaar.
85mm portret lens, zachte bokeh achtergrond,
[SECTOR] werkomgeving onscherp op achtergrond,
professionele editorial fotografie, hyperrealistisch 8K.
GEEN tekst, GEEN letters, GEEN watermark, GEEN logo in beeld.
geen AI-artefacten, geen vervorming, geen extra vingers.
```

Genereer 4 varianten (zelfde DNA, variatie in actie + emotie):
```
visual-1.png  →  Gefrustreerd naar laptop (probleem hook)
visual-2.png  →  Zelfverzekerd, armen licht gekruist (autoriteit)
visual-3.png  →  Glimlachend ontspannen (social proof)
visual-4.png  →  Wijst naar rechts buiten frame (CTA)
```

Opslagpad:
```
~/recruitin/meta-campaigns/assets/[CAMPAGNE_NAAM]/character.png
~/recruitin/meta-campaigns/assets/[CAMPAGNE_NAAM]/visual-1.png
~/recruitin/meta-campaigns/assets/[CAMPAGNE_NAAM]/visual-2.png
~/recruitin/meta-campaigns/assets/[CAMPAGNE_NAAM]/visual-3.png
~/recruitin/meta-campaigns/assets/[CAMPAGNE_NAAM]/visual-4.png
```

Slack: `🎨 [CAMPAGNE_NAAM] — Character image + 4 visuals klaar`

---

## TAAK 2 — DYNAMISCHE LANDING PAGE (per sector)

Elke sector krijgt een eigen pagina op een eigen subdomain.
Bestaande sectoren worden NIET opnieuw aangemaakt — check eerst:

```bash
# Check of subdomain al bestaat
curl -s -o /dev/null -w "%{http_code}" https://[sector_slug].kandidatentekort.nl
# 200 = bestaat al, skip deploy → ga direct naar TAAK 3
# 404 = nieuw, bouw pagina
```

### Sector-specifieke content mapping

```javascript
const SECTOR_DATA = {
  "oil-gas": {
    titel:      "Procesoperator",
    schaarste:  "8.5/10",
    doorloop:   "5,2 maanden",
    kosten:     "€21.400",
    pijnpunt:   "productie-uitval en veiligheidsrisico's door onderbezetting",
    stat1:      "73% van raffinaderijen heeft nu ≥1 kritieke vacature open",
    emoji:      "⚙️",
  },
  "constructie": {
    titel:      "Uitvoerder / Calculator",
    schaarste:  "9.1/10",
    doorloop:   "6,1 maanden",
    kosten:     "€24.800",
    pijnpunt:   "projectvertraging en boeteclausules door capaciteitstekort",
    stat1:      "81% van bouwbedrijven mist deadlines door personeelstekort",
    emoji:      "🏗️",
  },
  "automation": {
    titel:      "PLC / SCADA Engineer",
    schaarste:  "9.4/10",
    doorloop:   "7,0 maanden",
    kosten:     "€28.200",
    pijnpunt:   "stilstand van productielijnen en gemiste digitaliseringsprojecten",
    stat1:      "Slechts 340 PLC Engineers beschikbaar voor 1.200+ vacatures in NL",
    emoji:      "🤖",
  },
  "productie": {
    titel:      "Productie Teamleider",
    schaarste:  "7.8/10",
    doorloop:   "4,5 maanden",
    kosten:     "€18.600",
    pijnpunt:   "verhoogde uitval en kwaliteitsproblemen door rotatiedruk",
    stat1:      "68% van productiebedrijven draait op minimale bezetting",
    emoji:      "🏭",
  },
  "renewable-energy": {
    titel:      "Wind / Solar Technicus",
    schaarste:  "9.7/10",
    doorloop:   "8,3 maanden",
    kosten:     "€33.600",
    pijnpunt:   "vertraging van energietransitie projecten",
    stat1:      "Groei van 340% in vacatures, talent groeit 40%",
    emoji:      "🌱",
  },
}
```

### HTML template (volledig, één bestand)

Bouw `index.html` met deze structuur. Vervangt [PLACEHOLDERS] met
sector-specifieke waarden uit SECTOR_DATA hierboven.

```html
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Is jouw [TITEL] vacature al te lang open? | kandidatentekort.nl</title>

  <!-- Facebook Pixel -->
  <script>
  !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){
  n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window,document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '[META_PIXEL_ID]');
  fbq('track', 'PageView');
  </script>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">

  <style>
    :root {
      --bg:     #060708;
      --surf:   #0C0E13;
      --oranje: #E8630A;
      --tekst:  #DDE0EE;
      --grijs:  #2D2D2D;
      --muted:  #6B7280;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: var(--bg);
      color: var(--tekst);
      font-family: 'DM Sans', sans-serif;
      line-height: 1.6;
    }
    h1, h2, h3 {
      font-family: 'Bricolage Grotesque', sans-serif;
      font-weight: 700;
    }

    /* NAV */
    nav {
      padding: 1.2rem 2rem;
      border-bottom: 1px solid #1a1d24;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .logo {
      font-family: 'Bricolage Grotesque', sans-serif;
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--tekst);
      text-decoration: none;
    }
    .logo span { color: var(--oranje); }

    /* HERO */
    .hero {
      max-width: 860px;
      margin: 0 auto;
      padding: 5rem 2rem 3rem;
      text-align: center;
    }
    .sector-badge {
      display: inline-block;
      background: rgba(232, 99, 10, 0.12);
      border: 1px solid rgba(232, 99, 10, 0.3);
      color: var(--oranje);
      padding: 0.3rem 0.9rem;
      border-radius: 99px;
      font-size: 0.85rem;
      font-weight: 500;
      margin-bottom: 1.5rem;
    }
    h1 {
      font-size: clamp(2rem, 5vw, 3.2rem);
      line-height: 1.15;
      margin-bottom: 1.2rem;
      letter-spacing: -0.02em;
    }
    h1 em {
      color: var(--oranje);
      font-style: normal;
    }
    .sub {
      font-size: 1.15rem;
      color: #9CA3AF;
      max-width: 600px;
      margin: 0 auto 2.5rem;
    }
    .cta-btn {
      display: inline-block;
      background: var(--oranje);
      color: white;
      padding: 1rem 2.2rem;
      border-radius: 8px;
      font-size: 1.05rem;
      font-weight: 600;
      text-decoration: none;
      transition: opacity 0.2s;
      font-family: 'Bricolage Grotesque', sans-serif;
    }
    .cta-btn:hover { opacity: 0.88; }
    .trust {
      margin-top: 1.2rem;
      font-size: 0.82rem;
      color: var(--muted);
    }

    /* STATS */
    .stats {
      background: var(--surf);
      border-top: 1px solid #1a1d24;
      border-bottom: 1px solid #1a1d24;
      padding: 2.5rem 2rem;
      margin: 3rem 0;
    }
    .stats-inner {
      max-width: 860px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2rem;
      text-align: center;
    }
    .stat-num {
      font-family: 'Bricolage Grotesque', sans-serif;
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--oranje);
    }
    .stat-label {
      font-size: 0.88rem;
      color: var(--muted);
      margin-top: 0.3rem;
    }

    /* HOE HET WERKT */
    .hoe {
      max-width: 860px;
      margin: 0 auto;
      padding: 3rem 2rem;
    }
    .hoe h2 {
      font-size: 1.8rem;
      margin-bottom: 2rem;
      text-align: center;
    }
    .stappen {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
    }
    .stap {
      background: var(--surf);
      border: 1px solid #1a1d24;
      border-radius: 12px;
      padding: 1.5rem;
    }
    .stap-nr {
      font-family: 'Bricolage Grotesque', sans-serif;
      font-size: 2rem;
      font-weight: 700;
      color: var(--oranje);
      opacity: 0.4;
      line-height: 1;
      margin-bottom: 0.5rem;
    }
    .stap h3 { font-size: 1rem; margin-bottom: 0.4rem; }
    .stap p  { font-size: 0.88rem; color: var(--muted); }

    /* FORM SECTIE */
    .form-sectie {
      max-width: 760px;
      margin: 0 auto;
      padding: 3rem 2rem;
      text-align: center;
    }
    .form-sectie h2 {
      font-size: 1.8rem;
      margin-bottom: 0.6rem;
    }
    .form-sectie p {
      color: var(--muted);
      margin-bottom: 2rem;
      font-size: 0.95rem;
    }
    .jotform-wrapper {
      background: var(--surf);
      border: 1px solid #1a1d24;
      border-radius: 12px;
      overflow: hidden;
      min-height: 500px;
    }
    iframe {
      width: 100%;
      min-height: 500px;
      border: none;
    }

    /* SOCIAL PROOF */
    .proof {
      background: var(--surf);
      border-top: 1px solid #1a1d24;
      padding: 3rem 2rem;
      margin-top: 3rem;
    }
    .proof-inner {
      max-width: 760px;
      margin: 0 auto;
      text-align: center;
    }
    blockquote {
      font-size: 1.1rem;
      font-style: italic;
      color: var(--tekst);
      margin-bottom: 0.8rem;
    }
    cite {
      font-size: 0.85rem;
      color: var(--muted);
      font-style: normal;
    }

    /* FOOTER */
    footer {
      padding: 2rem;
      text-align: center;
      font-size: 0.8rem;
      color: var(--muted);
      border-top: 1px solid #1a1d24;
    }
    footer a { color: var(--muted); }

    @media (max-width: 640px) {
      .stats-inner { grid-template-columns: 1fr; gap: 1.5rem; }
      .stappen     { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

<nav>
  <a class="logo" href="/">kandidatentekort<span>.nl</span></a>
  <a class="cta-btn" href="#analyse" style="padding:0.6rem 1.2rem;font-size:0.9rem;">
    Gratis analyse →
  </a>
</nav>

<section class="hero">
  <div class="sector-badge">[EMOJI] [SECTOR] · [REGIO]</div>
  <h1>Is jouw <em>[TITEL]</em> vacature<br>al langer dan 6 weken open?</h1>
  <p class="sub">
    [SECTOR] bedrijven in [REGIO] kampen met extreme technische schaarste.
    Ontvang gratis een analyse van jouw wervingssituatie — binnen 10 minuten.
  </p>
  <a href="#analyse" class="cta-btn">Vraag gratis analyse aan →</a>
  <p class="trust">✓ Gratis &nbsp; ✓ Geen verplichtingen &nbsp; ✓ Binnen 10 min in je inbox</p>
</section>

<section class="stats">
  <div class="stats-inner">
    <div>
      <div class="stat-num">[SCHAARSTE]</div>
      <div class="stat-label">Schaarste-score<br>[SECTOR] technici</div>
    </div>
    <div>
      <div class="stat-num">[DOORLOOP]</div>
      <div class="stat-label">Gemiddelde doorlooptijd<br>open vacature</div>
    </div>
    <div>
      <div class="stat-num">[KOSTEN]</div>
      <div class="stat-label">Kosten per jaar<br>open vacature</div>
    </div>
  </div>
</section>

<section class="hoe">
  <h2>Hoe het werkt</h2>
  <div class="stappen">
    <div class="stap">
      <div class="stap-nr">01</div>
      <h3>Vul het formulier in</h3>
      <p>2 minuten. Functie, sector en regio — meer hebben we niet nodig.</p>
    </div>
    <div class="stap">
      <div class="stap-nr">02</div>
      <h3>Wij analyseren de markt</h3>
      <p>Ons systeem checkt beschikbaarheid, salaris en concurrentie voor jouw profiel.</p>
    </div>
    <div class="stap">
      <div class="stap-nr">03</div>
      <h3>Rapport in je inbox</h3>
      <p>Binnen 10 minuten ontvang je een persoonlijke arbeidsmarktanalyse.</p>
    </div>
  </div>
</section>

<section class="form-sectie" id="analyse">
  <h2>Vraag jouw gratis analyse aan</h2>
  <p>[STAT1]</p>
  <div class="jotform-wrapper">
    <iframe
      id="jotform"
      src="[JOTFORM_URL]?utm_source=landingpage&utm_campaign=[CAMPAGNE_NAAM]&sector=[SECTOR_SLUG]"
      scrolling="yes"
      allow="geolocation; microphone; camera">
    </iframe>
  </div>
</section>

<section class="proof">
  <div class="proof-inner">
    <blockquote>
      "Binnen 6 weken hadden we 3 gekwalificeerde kandidaten voor een rol
       die al 5 maanden openstond. De analyse gaf ons direct inzicht."
    </blockquote>
    <cite>— HR Manager, [SECTOR] bedrijf · [REGIO]</cite>
  </div>
</section>

<footer>
  <p>© 2026 Recruitin B.V. · Doesburg ·
    <a href="mailto:info@recruitin.nl">info@recruitin.nl</a> ·
    <a href="/privacy">Privacy</a>
  </p>
</footer>

<script>
  // Smooth scroll
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      document.querySelector(a.getAttribute('href'))
        ?.scrollIntoView({ behavior: 'smooth' });
    });
  });

  // Scroll depth tracking
  let tracked = {};
  window.addEventListener('scroll', () => {
    const pct = Math.round(
      (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
    );
    [25, 50, 75, 90].forEach(p => {
      if (pct >= p && !tracked[p]) {
        tracked[p] = true;
        fbq('trackCustom', 'ScrollDepth', { depth: p });
      }
    });
  });

  // Jotform Lead event
  window.addEventListener('message', e => {
    if (e.data && e.data.action === 'submission-completed') {
      fbq('track', 'Lead');
      gtag('event', 'generate_lead');
    }
  });
</script>
</body>
</html>
```

Vervang alle [PLACEHOLDERS] met sector-specifieke waarden uit SECTOR_DATA.

Deploy:
```bash
# Maak tijdelijke map aan
mkdir -p /tmp/lp-[SECTOR_SLUG]
cp ~/recruitin/landing-pages/[CAMPAGNE_NAAM]/index.html /tmp/lp-[SECTOR_SLUG]/

# Deploy via Netlify CLI met custom subdomain
netlify deploy --prod \
  --dir=/tmp/lp-[SECTOR_SLUG] \
  --site=[NETLIFY_SITE_ID_VOOR_DIT_SECTOR]

# Of maak nieuwe Netlify site aan via API:
curl -X POST https://api.netlify.com/api/v1/sites \
  -H "Authorization: Bearer [NETLIFY_TOKEN]" \
  -d '{"name":"kt-[sector_slug]","custom_domain":"[sector_slug].kandidatentekort.nl"}'
```

Sla de live URL op als: `LANDING_PAGE_URL`

Slack: `🌐 [CAMPAGNE_NAAM] — Landing page live: https://[sector_slug].kandidatentekort.nl`

---

## TAAK 3 — META CAMPAGNE (Marketing API)

Maak de volledige campagne aan via Meta Marketing API v21.0.
Status altijd PAUSED — Wouter activeert handmatig.

Ad copy gegenereerd op basis van sector + functie uit de payload:

```python
#!/usr/bin/env python3
# ~/recruitin/scripts/meta_campaign_builder.py

import os, json, requests
from datetime import datetime

BASE    = "https://graph.facebook.com/v21.0"
TOKEN   = os.getenv("META_ACCESS_TOKEN")
ACCOUNT = os.getenv("META_ACCOUNT_ID")   # act_XXXXXXXXXX
PIXEL   = os.getenv("META_PIXEL_ID")

def maak_campagne(sector, functie, regio, landing_url, campagne_naam):

    # 1 — Campaign
    r = requests.post(f"{BASE}/{ACCOUNT}/campaigns", data={
        "name":             campagne_naam,
        "objective":        "OUTCOME_LEADS",
        "status":           "PAUSED",
        "special_ad_categories": "[]",
        "access_token":     TOKEN,
    })
    campaign_id = r.json()["id"]
    print(f"Campaign ID: {campaign_id}")

    # 2 — Ad Sets
    adsets = [
        {
            "name":    f"{campagne_naam}_Prospecting",
            "budget":  60,  # % van dagbudget
            "targeting": {
                "geo_locations": {
                    "countries": ["NL"],
                    "regions": [{"key": "513"},   # Gelderland
                                {"key": "514"},   # Overijssel
                                {"key": "523"}],  # Noord-Brabant
                },
                "age_min": 28,
                "age_max": 62,
                "flexible_spec": [{
                    "job_title": [
                        {"id": "103285036402772", "name": "HR Manager"},
                        {"id": "105763682788297", "name": "HR Director"},
                        {"id": "102374656463855", "name": "Chief Executive Officer"},
                    ]
                }],
            }
        },
        {
            "name":    f"{campagne_naam}_Lookalike",
            "budget":  25,
            "targeting": {
                "geo_locations": {"countries": ["NL"]},
                "lookalike_specs": [{"ratio": 0.01, "country": "NL"}],
            }
        },
        {
            "name":    f"{campagne_naam}_Retargeting",
            "budget":  15,
            "targeting": {
                "geo_locations": {"countries": ["NL"]},
                "custom_audiences": [{"id": os.getenv("META_RETARGET_AUDIENCE_ID")}],
                "exclusions": {"custom_audiences": [{"id": os.getenv("META_LEADS_AUDIENCE_ID")}]},
            }
        },
    ]

    adset_ids = []
    daily_budget_cents = int(os.getenv("META_DAILY_BUDGET", "1700"))  # €17/dag

    for adset_cfg in adsets:
        r2 = requests.post(f"{BASE}/{ACCOUNT}/adsets", data={
            "name":              adset_cfg["name"],
            "campaign_id":       campaign_id,
            "daily_budget":      str(int(daily_budget_cents * adset_cfg["budget"] / 100)),
            "billing_event":     "IMPRESSIONS",
            "optimization_goal": "LEAD_GENERATION",
            "destination_type":  "WEBSITE",
            "promoted_object":   json.dumps({"pixel_id": PIXEL, "custom_event_type": "LEAD"}),
            "targeting":         json.dumps(adset_cfg["targeting"]),
            "status":            "PAUSED",
            "access_token":      TOKEN,
        })
        adset_id = r2.json().get("id")
        if adset_id:
            adset_ids.append(adset_id)
            print(f"  Ad Set: {adset_cfg['name']} → {adset_id}")

    # 3 — Ad Copy (4 varianten)
    copies = [
        {
            "visual": "visual-1.png",
            "headline": f"Is jouw {functie} vacature al te lang open?",
            "body": f"Elke maand zonder {functie} kost je direct geld.\n"
                    f"Productieverlies, overwerk, gemiste opdrachten.\n"
                    f"Bereken gratis jouw situatie.",
            "cta": "LEARN_MORE",
        },
        {
            "visual": "visual-2.png",
            "headline": f"{functie} vinden in {sector}? Score: {sector_schaarste(sector)}",
            "body": f"De {sector} arbeidsmarkt in {regio} staat onder extreme druk.\n"
                    f"Weet jij hoe schaars jouw profiel echt is?",
            "cta": "LEARN_MORE",
        },
        {
            "visual": "visual-3.png",
            "headline": f"6 weken. 3 kandidaten. {sector} bedrijf, {regio}.",
            "body": f"Zo snel kan het gaan als je weet waar je zoekt.\n"
                    f"Gratis arbeidsmarktanalyse voor jouw {functie} vacature.",
            "cta": "LEARN_MORE",
        },
        {
            "visual": "visual-4.png",
            "headline": f"Jouw concurrent werft al. Ben jij er klaar voor?",
            "body": f"{sector} bedrijven in {regio} kampen met recordschaarste.\n"
                    f"Gratis analyse — 10 minuten — direct in je inbox.",
            "cta": "LEARN_MORE",
        },
    ]

    # Upload images + maak ads aan
    ad_ids = []
    for i, copy in enumerate(copies):
        # Image upload (base_path)
        img_path = f"~/recruitin/meta-campaigns/assets/[CAMPAGNE_NAAM]/{copy['visual']}"

        # Image hash ophalen via API
        with open(os.path.expanduser(img_path), "rb") as f:
            img_r = requests.post(
                f"{BASE}/{ACCOUNT}/adimages",
                files={"filename": f},
                data={"access_token": TOKEN}
            )
        img_hash = list(img_r.json().get("images", {}).values())[0]["hash"]

        # Ad creative
        creative_r = requests.post(f"{BASE}/{ACCOUNT}/adcreatives", data={
            "name": f"{campagne_naam}_Creative_{i+1}",
            "object_story_spec": json.dumps({
                "page_id": os.getenv("META_PAGE_ID"),
                "link_data": {
                    "image_hash":  img_hash,
                    "link":        landing_url,
                    "message":     copy["body"],
                    "name":        copy["headline"],
                    "call_to_action": {
                        "type": copy["cta"],
                        "value": {"link": landing_url}
                    }
                }
            }),
            "access_token": TOKEN,
        })
        creative_id = creative_r.json().get("id")

        # Ad aanmaken (in eerste ad set)
        ad_r = requests.post(f"{BASE}/{ACCOUNT}/ads", data={
            "name":        f"{campagne_naam}_Ad_{i+1}",
            "adset_id":    adset_ids[0] if adset_ids else "",
            "creative":    json.dumps({"creative_id": creative_id}),
            "status":      "PAUSED",
            "access_token": TOKEN,
        })
        ad_id = ad_r.json().get("id")
        if ad_id:
            ad_ids.append(ad_id)
            print(f"  Ad {i+1}: {copy['headline'][:40]} → {ad_id}")

    # Opslaan
    ids = {
        "campagne_naam": campagne_naam,
        "campaign_id":   campaign_id,
        "adset_ids":     adset_ids,
        "ad_ids":        ad_ids,
        "landing_url":   landing_url,
        "timestamp":     datetime.now().isoformat(),
    }
    out = os.path.expanduser(f"~/recruitin/meta-campaigns/{campagne_naam}/campaign-ids.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(ids, f, indent=2)

    print(f"\n✅ Meta campagne klaar — {campaign_id}")
    return ids

def sector_schaarste(sector):
    mapping = {
        "oil & gas": "8.5/10", "constructie": "9.1/10",
        "automation": "9.4/10", "productie": "7.8/10",
        "renewable energy": "9.7/10",
    }
    return mapping.get(sector.lower(), "8.0/10")

if __name__ == "__main__":
    import sys
    maak_campagne(
        sector=sys.argv[1],
        functie=sys.argv[2],
        regio=sys.argv[3],
        landing_url=sys.argv[4],
        campagne_naam=sys.argv[5],
    )
```

Voer uit:
```bash
python3 ~/recruitin/scripts/meta_campaign_builder.py \
  "[SECTOR]" "[FUNCTIE]" "[REGIO]" "[LANDING_URL]" "[CAMPAGNE_NAAM]"
```

Slack: `📣 [CAMPAGNE_NAAM] — Meta campagne aangemaakt (PAUSED) — ID: [ID]`

---

## TAAK 4 — KLING VIDEO CLIPS

```bash
python3 ~/recruitin/scripts/kling_invideo_pipeline.py \
  --image ~/recruitin/meta-campaigns/assets/[CAMPAGNE_NAAM]/character.png \
  --campagne [CAMPAGNE_NAAM] \
  --sector "[SECTOR]" \
  --duur 5 \
  --formaat 1:1
```

Wacht tot klaar (±15 min). Controleer:
- `scene_01.mp4` ✓
- `scene_02.mp4` ✓
- `scene_03.mp4` ✓
- `invideo_instructie.md` ✓

Slack: `🎬 [CAMPAGNE_NAAM] — 3 Kling clips klaar`

---

## EINDRAPPORT (na alle taken)

```
╔═══════════════════════════════════════════════════╗
║  CAMPAGNE AUTOMATION KLAAR                       ║
║  [CAMPAGNE_NAAM]                                 ║
╠═══════════════════════════════════════════════════╣
║  Trigger   : Jotform — [NAAM] ([EMAIL])          ║
║  Bedrijf   : [BEDRIJF]                           ║
║  Sector    : [SECTOR] · [REGIO]                  ║
╠═══════════════════════════════════════════════════╣
║  ✅ Character + 4 ad visuals gegenereerd         ║
║  ✅ Landing page: [LANDING_URL]                  ║
║  ✅ Meta campagne PAUSED — [CAMPAIGN_ID]         ║
║  ✅ Kling clips: scene_01/02/03.mp4              ║
║  ⏳ InVideo assembly: handmatig (2 min)          ║
╠═══════════════════════════════════════════════════╣
║  JOUW ACTIES (5 min totaal):                     ║
║  □ InVideo: plak instructie.md in Claude.ai      ║
║  □ Controleer landing page op mobiel             ║
║  □ Zet Meta campagne op ACTIVE                   ║
╚═══════════════════════════════════════════════════╝
```

Slack eindmelding:
```
🚀 *Campagne klaar: [CAMPAGNE_NAAM]*
👤 Aanvrager: [NAAM] · [BEDRIJF]
🌐 Landing: [LANDING_URL]
📣 Meta: PAUSED · [CAMPAIGN_ID]
🎬 Kling clips: klaar voor InVideo
⏱️ Totale tijd: [X] minuten
```

---

## FOUTAFHANDELING

```
Kling clip mislukt →  Retry max 2x met 60s wachttijd
Netlify deploy fout → Probeer Vercel als fallback
Meta API 400 error  → Log error + ga door met andere taken
                      Stuur Slack alert met foutmelding
Image generatie fout→ Gebruik fallback placeholder image
                      Noteer: handmatig vervangen voor Meta upload
```

---

## CLAUDE.MD REFERENTIE

Antigravity leest altijd eerst: `~/recruitin/.claude/CLAUDE.md`
Alle keys, paden en sector data staan daar gedocumenteerd.
Bij conflict: CLAUDE.md heeft prioriteit boven dit prompt.
