# JobDigger HQ - Recruitment Lead Intelligence Platform

## Purpose
JobDigger HQ is een geautomatiseerd systeem voor het identificeren, scrapen en kwalificeren van recruitment leads via vacature-analyse. Het platform transformeert openbare vacatures in gekwalificeerde sales leads voor Recruitin.

## Core Functionality

### 1. Vacature Scraping
- Automatisch scrapen van vacatures van job boards (Indeed, LinkedIn Jobs, Monsterboard, etc.)
- Tracking van nieuwe vacatures bij target bedrijven
- Identificatie van recruitment needs op basis van vacature-volume en -types

### 2. Lead Qualification
- Analyse van vacature-teksten voor tech stack, seniority, urgentie
- Bedrijfsgrootte en sector identificatie
- Lead scoring op basis van ICP (Ideal Customer Profile)
- Prioritering voor sales outreach

### 3. Intelligence Gathering
- Recruitment pain points detectie uit vacature-teksten
- Concurrent analysis (welke bureaus werken al met target)
- Hiring velocity tracking (hoe snel groeit een bedrijf)
- Budget indicatoren uit vacature-informatie

### 4. Pipedrive Integration
- Automatische lead import in Pipedrive
- Deal creation met relevante context
- Activity scheduling voor sales follow-up
- Custom fields update met intelligence data

## Integration Points

### Input Sources
- **Job Boards**: Indeed, LinkedIn Jobs, Monsterboard, Nationale Vacaturebank
- **Company Career Pages**: Direct scraping van target bedrijven
- **LinkedIn**: Job postings via LinkedIn API
- **Google Jobs**: Via search scraping

### Output Destinations
- **Pipedrive**: Lead en deal creation
- **Google Sheets**: Analytics en rapportage
- **Slack**: Real-time notificaties voor high-value leads
- **Email**: Daily digest van nieuwe opportunities

## Cowork Integration
Cowork fungeert als centrale orchestration layer:
- **Workflow triggers**: Nieuwe vacature detected → Lead creation → Outreach scheduling
- **Team collaboration**: Sales ziet real-time welke leads worden verwerkt
- **Task assignment**: Auto-assign leads op basis van sector/specialisatie
- **Quality control**: Review workflow voor low-confidence leads

## Key Metrics

### Efficiency
- Vacatures gescraped per dag: Target 500+
- Leads gecreëerd per week: Target 50+
- Lead-to-opportunity conversion: Target 15%
- Time saved vs manual research: 20+ hrs/week

### Quality
- Lead score accuracy: Target 85%+
- False positive rate: Target <10%
- Pipedrive data completeness: Target 95%+

## Usage Guidelines

### Daily Workflow
1. **Morning**: Review overnight scraping results (high-priority leads)
2. **Midday**: Analyze new target company vacatures
3. **Afternoon**: Export doelgroepen rapporten voor sales team
4. **Evening**: Schedule automated scraping voor next day

### Lead Prioritization
**Tier 1 (Hot)**:
- 5+ vacatures bij target bedrijf
- Tech roles met scarce skills
- Urgente hiring (keywords: asap, immediately, urgent)

**Tier 2 (Warm)**:
- 2-4 vacatures
- Standard tech roles
- Normal hiring timeline

**Tier 3 (Cold)**:
- Single vacancy
- Non-tech support roles
- Long-term planning hires

## File Structure
```
JobDigger_HQ/
├── README.md (this file)
├── scraping_config.md (scraping parameters)
├── lead_qualification.md (scoring criteria)
├── pipedrive_integration.md (API specs)
├── cowork_workflows.md (automation flows)
└── target_companies.md (ICP definition)
```

## Version
- **Created**: 2026-01-18
- **Last Updated**: 2026-01-18
- **Owner**: Wouter Arts, Recruitin B.V.
