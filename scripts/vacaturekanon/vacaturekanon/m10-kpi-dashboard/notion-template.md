# Notion Template Schemas — Vacaturekanon KPI Tracking

> Drie databases voor volledig operationeel KPI-beheer.
> Kopieer deze structuren naar Notion als nieuwe database.

---

## Database 1: Klanten

**Database naam:** `VK — Klanten`

| Veld | Type | Opties / Formule |
|------|------|-----------------|
| Bedrijfsnaam | Titel | — |
| Sector | Select | Oil & Gas · Constructie · Productie · Automation · Renewable Energy |
| Regio | Select | Gelderland · Overijssel · Noord-Brabant · Overig |
| Pakket | Select | Starter · Groei · Scale |
| Status | Select | Prospect · Intake · Actief · Afgerond · Churned |
| Start datum | Date | — |
| Eind datum | Date | — |
| Contactpersoon | Text | — |
| Email | Email | — |
| Telefoon | Phone | — |
| Pipedrive Deal ID | Number | — |
| Contractwaarde | Number | Format: Euro |
| Betaald | Checkbox | — |
| Notities | Text | — |
| Campagnes | Relation | → Database 2: Campagnes |

---

## Database 2: Campagnes

**Database naam:** `VK — Campagnes`

| Veld | Type | Opties / Formule |
|------|------|-----------------|
| Campagne naam | Titel | Formaat: VK-[SECTOR]-[bedrijfsnaam] |
| Klant | Relation | → Database 1: Klanten |
| Sector | Select | Oil & Gas · Constructie · Productie · Automation · Renewable Energy |
| Functietitel | Text | Bijv. "PLC Programmeur" |
| Status | Select | Voorbereiding · Live · Gepauzeerd · Afgerond · Garantie-verlenging |
| Start datum | Date | — |
| Live datum | Date | Dag 5 na start |
| Deadline | Date | Start + 21 dagen |
| Meta campagne ID | Text | — |
| Meta ad account ID | Text | — |
| Landingspagina URL | URL | — |
| Pixel ID | Text | — |
| Budget per maand | Number | Format: Euro |
| Budget besteed | Number | Format: Euro |
| Bereik | Number | — |
| Impressies | Number | — |
| Klikken | Number | — |
| CTR | Formula | `prop("Klikken") / prop("Impressies") * 100` |
| Leads | Number | — |
| CPL | Formula | `prop("Budget besteed") / prop("Leads")` |
| Kandidaten aangeleverd | Number | — |
| Interviews | Number | — |
| Aannames | Number | — |
| Gevuld op dag | Number | — |
| Top ad variant | Select | Variant-A · Variant-B · Variant-C |
| Wekelijkse rapporten | Relation | → Database 3: Weekrapporten |
| Intern notities | Text | — |

---

## Database 3: Weekrapporten

**Database naam:** `VK — Weekrapporten`

| Veld | Type | Opties / Formule |
|------|------|-----------------|
| Week | Titel | Formaat: "Week 12 — VoorbeeldBV" |
| Campagne | Relation | → Database 2: Campagnes |
| Week nummer | Number | — |
| Datum van | Date | — |
| Datum tot | Date | — |
| Budget besteed | Number | Format: Euro |
| Bereik | Number | — |
| Impressies | Number | — |
| Klikken | Number | — |
| CTR | Formula | `prop("Klikken") / prop("Impressies") * 100` |
| Leads | Number | — |
| CPL | Formula | `prop("Budget besteed") / prop("Leads")` |
| Video views | Number | — |
| Video completion pct | Number | Format: Percentage |
| Top ad | Text | — |
| Frequentie | Number | — |
| Kandidaten aangeleverd | Number | — |
| Status | Select | Op schema · Aandacht vereist · Kritisch |
| Aanbeveling | Text | — |
| Rapport verstuurd | Checkbox | — |
| Rapport URL | URL | Google Docs link |

---

## Automatisering via Zapier / Make

### Trigger 1: Nieuwe campagne aanmaken
- **Trigger:** Nieuwe deal in Pipedrive (stage "Intake Goedgekeurd")
- **Actie:** Maak record aan in Notion Database 2 (Campagnes)
- **Velden:** Klant naam, sector, functietitel, startdatum = vandaag

### Trigger 2: Wekelijks rapport
- **Trigger:** Elke vrijdag 17:00
- **Actie 1:** Haal Meta Ads data op via Marketing API
- **Actie 2:** Maak weekrapport aan in Database 3
- **Actie 3:** Stuur email naar klant met rapport PDF (via Resend)

### Trigger 3: Campagne afgerond
- **Trigger:** Status "Afgerond" gezet in Database 2
- **Actie:** Update Pipedrive deal naar stage "Afgerond"
- **Actie:** Stuur tevredenheidsmail via Resend

---

## KPI Drempelwaarden (automatische status)

```
Status "Op schema":
  CTR ≥ 0.8% EN CPL ≤ €25 EN Frequentie ≤ 3

Status "Aandacht vereist":
  CTR < 0.8% OF CPL > €25 OF Frequentie > 3

Status "Kritisch":
  CTR < 0.5% voor 3+ dagen
  OF CPL > €40
  OF Frequentie > 4
  OF Dag 14 zonder leads
```
