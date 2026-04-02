# Apollo Outreach Sequence — Vacaturekanon

> 5-touch cold outreach over 14 dagen.
> Doelgroep: HR-beslissers en DGA's bij technische bedrijven (ICP uit `apollo-filters.json`).
> Doel: demo/gesprek boeken of intake-formulier laten invullen.

**Regels:**
- Altijd vanuit Wouter persoonlijk (geen bedrijfsnaam als afzender)
- Maximaal 125 tekens preview-tekst voor mobile
- Ondertekening: altijd `Wouter` — nooit "Met vriendelijke groet", nooit bedrijfsnaam
- VERBODEN woorden: sparren, nieuwsgierig, indrukwekkend, viel me op, past perfect
- Primaire CTA: vrijblijvend gesprek / intake-link — nooit direct voorstel sturen

---

## Touch 1 — Dag 1: Eerste email (problema-eerste benadering)

**Onderwerp varianten (A/B test):**
- A: `{{bedrijfsnaam}} — {{functietitel}} vacature`
- B: `Openstaande {{functietitel}} vacature bij {{bedrijfsnaam}}`
- C: `{{voornaam}}, jullie {{functietitel}} vacature`

**Body:**

```
Hoi {{voornaam}},

Zag dat {{bedrijfsnaam}} op zoek is naar een {{functietitel}}.

In de {{sector}} markt staan dit soort vacatures gemiddeld 67 dagen open via traditionele kanalen — omdat de goede kandidaten simpelweg niet op Jobboard.nl kijken.

Wij vullen ze in 3 weken via gerichte social media campagnes — gericht op passieve kandidaten in {{regio}}.

Zou een kort gesprek van 15 minuten interessant zijn?

Wouter
```

**Personalisatievelden:** `{{voornaam}}`, `{{bedrijfsnaam}}`, `{{functietitel}}`, `{{sector}}`, `{{regio}}`

**Timing:** Dinsdag–donderdag, 08:30–10:00 of 14:00–15:30

---

## Touch 2 — Dag 3: Follow-up (sociaal bewijs)

**Onderwerp varianten:**
- A: `Re: {{functietitel}} vacature`
- B: `18 dagen — {{bedrijfsnaam}}`

**Body:**

```
Hoi {{voornaam}},

Korte follow-up op mijn email van maandag.

Ter illustratie: we vulden vorige maand een {{vergelijkbare_functie}} vacature voor een {{vergelijkbare_sector}} bedrijf in {{regio}} in 18 dagen. De kandidaat is aangenomen en werkt er nu.

Kosten: €2.750 all-in (inclusief advertentiebudget).

Vergelijk dat met wat een bureau rekent bij een aanname.

Werkt een bel van 15 minuten deze week?

Wouter
```

**Personalisatievelden:** `{{voornaam}}`, `{{vergelijkbare_functie}}` (manueel of via sector-mapping), `{{vergelijkbare_sector}}`, `{{regio}}`

---

## Touch 3 — Dag 6: Waarde-email (data)

**Onderwerp varianten:**
- A: `Wat kost die openstaande vacature per dag?`
- B: `{{functietitel}} markt: de cijfers`

**Body:**

```
{{voornaam}},

Snelle rekensom voor jullie situatie:

Elke dag dat een {{functietitel}} vacature openstaat kost een technisch bedrijf gemiddeld €800–€1.500 aan productiviteitsverlies (overuren, uitgestelde projecten, overbelasting team).

Bij 67 dagen (de marktgemiddelde doorlooptijd): €53.600–€100.500 verlies.

Onze campagne kost €2.750 en vult gemiddeld in 21 dagen.

Dat is een verschil van €36.800–€73.000 aan vermeden verlies.

Heeft dit zin om kort te bespreken?

Wouter

P.S. Je kunt ook direct de intake invullen: vacaturekanon.nl/intake — duurt 5 minuten.
```

**Personalisatievelden:** `{{voornaam}}`, `{{functietitel}}`

---

## Touch 4 — Dag 10: Alternatieve CTA (lage drempel)

**Onderwerp varianten:**
- A: `Niet het juiste moment?`
- B: `Alleen als het relevant is, {{voornaam}}`

**Body:**

```
{{voornaam}},

Begrijp dat het druk is of dat dit misschien niet het juiste moment is.

Twee opties:

1. Gratis intake (5 min) → vacaturekanon.nl/intake
   Je ontvangt binnen 24 uur een voorstel op maat — geheel vrijblijvend.

2. Later → Stuur me een mail en ik neem over 4 weken opnieuw contact op.

Geen reactie = ik stop na deze email. Geen verdere follow-up.

Wouter
```

**Personalisatievelden:** `{{voornaam}}`

---

## Touch 5 — Dag 14: Breakup email

**Onderwerp varianten:**
- A: `Laatste bericht — {{bedrijfsnaam}}`
- B: `Sluit ik af, {{voornaam}}`

**Body:**

```
{{voornaam}},

Dit is mijn laatste bericht over de {{functietitel}} vacature bij {{bedrijfsnaam}}.

Als de timing niet klopt of als jullie het al opgelost hebben: top, dan wens ik jullie succes.

Mocht je in de toekomst een moeilijk in te vullen technische functie hebben, denk dan aan ons: vacaturekanon.nl

Tot dan.

Wouter
```

**Personalisatievelden:** `{{voornaam}}`, `{{functietitel}}`, `{{bedrijfsnaam}}`

---

## Lemlist / Apollo sequence instellingen

```json
{
  "sequence_naam": "VK-Apollo-Outreach-v1",
  "stappen": [
    { "dag": 1,  "kanaal": "email", "touch": 1, "template": "Touch1-Probleem" },
    { "dag": 3,  "kanaal": "email", "touch": 2, "template": "Touch2-SociaalBewijs" },
    { "dag": 6,  "kanaal": "email", "touch": 3, "template": "Touch3-Data" },
    { "dag": 10, "kanaal": "email", "touch": 4, "template": "Touch4-Lage-Drempel" },
    { "dag": 14, "kanaal": "email", "touch": 5, "template": "Touch5-Breakup" }
  ],
  "stop_bij_reply": true,
  "stop_bij_klik": false,
  "stop_bij_open": false,
  "verzend_tijden": {
    "dagen": ["maandag", "dinsdag", "woensdag", "donderdag"],
    "tijdvensters": ["08:30-10:00", "14:00-15:30"]
  },
  "max_emails_per_dag": 50,
  "tracking": {
    "opens": true,
    "clicks": true,
    "replies": true
  }
}
```

---

## Personalisatie-mapping per sector

| Sector | `{{sector}}` | `{{vergelijkbare_functie}}` | `{{vergelijkbare_sector}}` |
|--------|-------------|----------------------------|---------------------------|
| Oil & Gas | oil & gas sector | Process Engineer | raffinaderij |
| Constructie & Infra | bouwsector | Werkvoorbereider | infraproject |
| Productie & Manufacturing | maakindustrie | CNC Operator | productiebedrijf |
| Automation & High Tech | automation sector | PLC Programmeur | machinebouwer |
| Renewable Energy | renewable energy sector | Solar Engineer | windenergiebedrijf |

---

## KPI targets voor deze sequence

| Metric | Doel | Actie bij onderschrijding |
|--------|------|--------------------------|
| Open rate Touch 1 | >40% | Test ander onderwerp (variant B/C) |
| Reply rate totaal | >5% | Herschrijf Touch 1 body |
| Positieve replies | >2% van total | Analyseer welke touch converteert |
| Intake-invullers | >1% van total | Voeg directe link eerder toe (Touch 2) |
| Unsubscribes | <1% | Verfijn ICP targeting |

**Definitie positieve reply:** Interesse in gesprek, vraag om meer info, of intake ingevuld.
**Definitie negatieve reply:** Afmelding, "niet relevant", of boze reactie.

---

## Handmatige stappen na positieve reply

1. Beantwoord binnen 4 werkuren (niet geautomatiseerd)
2. Stel 15-minuten Calendly-link voor: `calendly.com/vacaturekanon/intake`
3. Stuur na gesprek direct intake-formulier als opvolging
4. Voeg toe aan Pipedrive: stage "Prospecting → Gesprek Gepland"
5. Stuur bevestigingsemail met voorstel binnen 24 uur na gesprek
