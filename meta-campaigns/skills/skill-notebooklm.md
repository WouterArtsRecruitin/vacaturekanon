# Skill: NotebookLM Marktonderzoek

## Doel
5 gestructureerde prompts genereren voor NotebookLM om diepgaand doelgroeponderzoek te doen
per sector/functie combinatie. Output wordt gebruikt als input voor ad copy generatie.

---

## Bronnen Strategie (voeg toe aan NotebookLM notebook)

### Verplichte bronnen
1. **LinkedIn vacatures** — zoek `{functie} {sector}` op LinkedIn Jobs, sla 10-15 vacature-URL's op
2. **Brancherapporten** — afhankelijk van sector:
   - Oil & Gas: Nogepa jaarrapport, TNO energie rapporten
   - Constructie: BouwKennis, EIB Economisch Instituut voor de Bouw
   - Productie/Automation: FME, Metaalunie, CBS arbeidsmarkt techniek
   - Renewable Energy: Holland Solar, Nederlandse WindEnergie Associatie
3. **CAO samenvatting** — zoek `CAO {sector} 2024 samenvatting PDF`
4. **Forum threads** — Reddit r/Netherlands, Werkenden.nl, Monsterboard reviews
5. **Concurrentie vacatures** — 5 vacatureteksten van concurrerende bedrijven

### Optionele bronnen
- Glassdoor reviews voor bedrijven in sector
- CBS arbeidsmarktdata technische beroepen
- Randstad / Manpower marktrapport

---

## De 5 Vaste Prompts

### Prompt 1 — Uitdagingen bij werving
```
Wat zijn de 3 grootste uitdagingen bij het werven van {functie} in de {sector} sector
in {regio} in 2025? Noem concrete pijnpunten voor zowel werkgevers als kandidaten.
```

### Prompt 2 — Bezwaren
```
Wat zijn de meest gehoorde bezwaren van {functie} professionals bij een nieuwe baan
in de {sector} industrie? Wat houdt ze tegen om te solliciteren of te switchen?
```

### Prompt 3 — Vakjargon & identiteit
```
Welk specifiek vakjargon, tools, certificaten en dagelijkse werkzaamheden
definiëren een {functie} in de {sector} sector? Gebruik hun eigen taal.
```

### Prompt 4 — Switchmotieven
```
Wat motiveert {functie} professionals in {sector} om van werkgever te wisselen?
Beschrijf de top 5 push-factoren (waarom ze weggaan) en pull-factoren (waarom ze komen).
```

### Prompt 5 — Ideale werkgever
```
Beschrijf de ideale werkgever vanuit het perspectief van een ervaren {functie}
in de {sector} industrie in Nederland. Wat zijn dealbreakers, wat zijn droomsituaties?
```

---

## Output verwerking

Sla NotebookLM antwoorden op als:
`campaigns/{campagne_naam}/notebooklm-research.md`

Structuur van het bestand:
```markdown
# NotebookLM Research — {campagne}

## Uitdagingen werving
[Prompt 1 antwoord]

## Bezwaren doelgroep
[Prompt 2 antwoord]

## Vakjargon & identiteit
[Prompt 3 antwoord]

## Switchmotieven
[Prompt 4 antwoord]

## Ideale werkgever
[Prompt 5 antwoord]

## Key insights (samenvatting)
- [3-5 bullet points voor gebruik in ad copy]
```

---

## Sector-specifieke bronnen

| Sector | Primaire bron | Secundaire bron |
|--------|---------------|-----------------|
| Oil & Gas | nogepa.nl | offshore-matters.nl |
| Constructie | bouwkennis.nl | eib.nl |
| Productie | fme.nl | metaalunie.nl |
| Automation | techniekneederland.nl | agv.nl |
| Renewable Energy | hollandsolar.nl | nwea.nl |

---

## Tips

- Gebruik NotebookLM met bronnen in het **Nederlands** voor betere resultaten
- Voer prompts 1 voor 1 in — wacht op volledig antwoord voor de volgende
- Vraag door bij vage antwoorden: "Geef concrete voorbeelden uit de praktijk"
- Bewaar de ruwe output — Agent 03 gebruikt deze als context
