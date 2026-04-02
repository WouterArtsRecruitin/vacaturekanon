# Skill: Meta Marketing API — Campagne Structuur

## API Overzicht

| Endpoint | Doel |
|----------|------|
| `POST /act_{id}/campaigns` | Campagne aanmaken |
| `POST /act_{id}/adsets` | Ad set aanmaken |
| `POST /act_{id}/adcreatives` | Creative aanmaken |
| `POST /act_{id}/ads` | Ad aanmaken |
| `POST /act_{id}/adimages` | Afbeelding uploaden |
| `GET /me/accounts` | Pagina-ID ophalen |

API versie: v20.0
Base URL: `https://graph.facebook.com/v20.0`

---

## Campagne Hiërarchie

```
Campagne (PAUSED)
  ├── Ad Set: Prospecting (60% budget)
  │     ├── Ad: schaarste
  │     ├── Ad: kosten
  │     ├── Ad: social_proof
  │     └── Ad: urgentie
  ├── Ad Set: Lookalike (25% budget)
  │     └── [zelfde 4 ads]
  └── Ad Set: Retargeting (15% budget)
        └── [zelfde 4 ads]
```

Totaal: 1 campagne → 3 ad sets → 12 ads

---

## Ad Set Targeting

### Prospecting (brede doelgroep)
```json
{
  "geo_locations": {
    "regions": [{"key": "aDxjiZAbub"}],
    "location_types": ["home", "recent"]
  },
  "age_min": 25,
  "age_max": 55,
  "locales": [24],
  "flexible_spec": [{
    "interests": [
      {"id": "6003139266461", "name": "Engineering"},
      {"id": "6003397425735", "name": "Manufacturing"}
    ]
  }]
}
```

### Lookalike (vergelijkbaar publiek)
- Vereist: Custom Audience op basis van conversies of klantlijst
- `custom_audiences: [{"id": "{LOOKALIKE_AUDIENCE_ID}"}]`
- Maak Lookalike aan in Meta Ads Manager: Audiences → Create → Lookalike

### Retargeting
- Vereist: Meta Pixel actief op landingspagina (JotForm)
- Custom audience: Website visitors laatste 30 dagen
- `custom_audiences: [{"id": "{PIXEL_RETARGET_AUDIENCE_ID}"}]`

---

## Budget Berekening

```
Dagelijks totaalbudget:
  Prospecting = dagbudget * 0.60
  Lookalike   = dagbudget * 0.25
  Retargeting = dagbudget * 0.15

Budget in API = euro * 100 (cents)
Voorbeeld: €30/dag → 3000 (API waarde)
```

### Budget presets

| Preset | Dag | Maand | Verwacht leads/maand |
|--------|-----|-------|----------------------|
| Klein  | €15 | €450  | 8-20 (CPL €22-55) |
| Medium | €30 | €900  | 15-40 (CPL €22-55) |
| Groot  | €60 | €1800 | 30-80 (CPL €22-55) |

---

## KPI Benchmarks (recruitment, NL)

| KPI | Goed | Acceptabel | Pauzeer |
|-----|------|------------|---------|
| CPL | <€40 | €40-60 | >€60 |
| CTR | >1.2% | 0.8-1.2% | <0.8% |
| CPC | <€1.50 | €1.50-3 | >€3 |
| Frequency | <3x | 3-5x | >5x |
| Relevance score | 7-10 | 4-6 | <4 |

---

## Campagne Doelstelling

```python
# Voor lead gen via JotForm:
{
    "objective": "OUTCOME_LEADS",
    "status": "PAUSED",
    "special_ad_categories": []
}

# Optimization goal per ad set:
"optimization_goal": "LEAD_GENERATION"
"billing_event": "IMPRESSIONS"
"bid_strategy": "LOWEST_COST_WITHOUT_CAP"
```

---

## Creative Structuur (per ad)

```python
{
    "name": "{campagne} | {ad_set_type} | {ad_type}",
    "object_story_spec": {
        "page_id": "{PAGE_ID}",
        "link_data": {
            "image_hash": "{IMAGE_HASH}",
            "link": "https://form.jotform.com/{JOTFORM_ID}",
            "message": "{primary_text}",     # max 125 tekens
            "name": "{headline}",            # max 40 tekens
            "description": "{description}",  # max 30 tekens
            "call_to_action": {"type": "APPLY_NOW"}
        }
    }
}
```

### CTA opties voor recruitment
- `APPLY_NOW` — standaard voor vacatures
- `LEARN_MORE` — voor awareness fase
- `SIGN_UP` — als je een formulier framed als aanmelding
- `GET_QUOTE` — voor salarisindicatie flow

---

## Image Hash Upload

```python
# Upload PNG naar Meta, krijg hash terug
POST /act_{account_id}/adimages
Content-Type: multipart/form-data
{
    "filename": "schaarste.png",  # als key
    "bestandsdata": <binary>
}

# Response:
{
    "images": {
        "schaarste.png": {
            "hash": "abc123...",
            "url": "https://...",
            "width": 1080,
            "height": 1080
        }
    }
}
```

---

## Monitoring & Optimalisatie

### Dagelijkse checks (kt-daily-monitor.py)
```python
GET /act_{account_id}/insights
params:
  date_preset: today
  fields: spend, impressions, clicks, actions, ctr, cpc, cpm
  level: adset
```

### Automatische acties
```
CPL > €60 → pauzeer ad set (status: PAUSED)
CTR < 0.8% → flag voor review
Frequency > 5 → verbreed audience of refresh creative
CPL < €15 → verhoog budget met 20% (schaalmogelijkheid)
```

---

## Env Vars

```bash
META_ACCESS_TOKEN    # Long-lived user token (60 dagen geldig)
META_ACCOUNT_ID      # Format: act_XXXXXXX of alleen XXXXXXX
META_PIXEL_ID        # Pixel voor conversie tracking
JOTFORM_FORM_ID      # Formulier ID voor leadgen
ANTHROPIC_API_KEY    # Voor ad copy generatie
```

### Token verlengen
```bash
# Verlengen via Graph API Explorer:
# https://developers.facebook.com/tools/explorer/
# Permissions: ads_management, ads_read, pages_manage_ads
```

---

## Audience IDs aanmaken (handmatig, eenmalig)

1. **Pixel retargeting audience:**
   Meta Ads Manager → Audiences → Create → Custom Audience → Website
   → All website visitors → 30 days → Sla op als "Website Visitors 30d"

2. **Lookalike audience:**
   Meta Ads Manager → Audiences → Create → Lookalike
   → Source: Leads (pixel), Country: NL, Size: 1%
   → Sla op als "Lookalike 1% NL Leads"

3. Kopieer beide audience IDs naar `campaign-input.json`

---

## Troubleshooting

| Fout | Oorzaak | Oplossing |
|------|---------|-----------|
| `(#100) param invalid` | Verkeerd account ID formaat | Gebruik zonder `act_` prefix |
| `(#200) permission denied` | Token mist ads_management | Genereer nieuwe token met juiste permissions |
| `(#368) blocked` | Special ad category vereist | Voeg `EMPLOYMENT` toe aan special_ad_categories |
| `(#1487470)` image rejected | PNG te klein of verkeerd formaat | Controleer: 1080x1080px, <30MB |
| Rate limit | Te veel calls | Wacht 60s, gebruik batch requests |

### Employment Special Ad Category
Voor recruitment advertenties in sommige regio's (VS/EU) vereist Meta:
```python
"special_ad_categories": ["EMPLOYMENT"]
```
Dit beperkt targeting opties. Test eerst zonder, voeg toe als Meta dit vereist.
