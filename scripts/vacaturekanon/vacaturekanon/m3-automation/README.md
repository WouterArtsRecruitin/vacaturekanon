# M3 — Template Builder

Vult `prospect-template.html` of `kandidaat-template.html` met data uit een JSON bestand.

## Installatie

```bash
npm install
```

## Gebruik

```bash
# Prospect pagina (voor potentiële klanten)
node template-builder.js --type prospect --input data.json --output output/prospect.html

# Kandidaat pagina (vacaturepagina)
node template-builder.js --type kandidaat --input vacancy.json --output output/vacancy.html

# Via npm scripts
npm run build:prospect
npm run build:kandidaat
```

## Template map

Plaats de HTML templates in een `templates/` submap:

```
m3-automation/
├── templates/
│   ├── prospect-template.html   ← kopieer vanuit m2-templates/
│   └── kandidaat-template.html  ← kopieer vanuit m2-templates/
├── template-builder.js
├── sector-data.json
├── example-prospect.json
└── example-kandidaat.json
```

## Verplichte velden

### Prospect
`bedrijfsnaam`, `sector`, `doelgroep_functietitels`, `regio`, `usps_werkgever`, `JOTFORM_URL`, `CALENDLY_URL`

### Kandidaat
`functietitel`, `bedrijfsnaam`, `regio`, `salaris_range`, `contract_type`, `sector`, `sollicitatie_url`

## Optionele velden met defaults

| Veld | Default |
|------|---------|
| `avg_time_to_hire` | Uit sector-data.json (bijv. "71" voor Automation) |
| `PIXEL_ID` | `REPLACE_WITH_PIXEL_ID` |
| `GA4_ID` | `REPLACE_WITH_GA4_ID` |
| `opdrachtgever_kleur_primary` | `#1A3F6F` |
| `date_posted` | Datum van vandaag |

## Sector data

`sector-data.json` bevat per sector:
- `avg_time_to_hire` — automatisch ingevuld als niet opgegeven
- `avg_salary_range`, `common_titles`, `usps_suggestions`
- `market_insight` voor in de template content
