#!/usr/bin/env python3
"""
Agent 03 — Campaign Input Builder
Interactief bouwen van campaign-input.md op basis van NotebookLM onderzoek.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CAMPAIGNS_DIR = BASE_DIR / "campaigns"

SECTOREN = ["Oil & Gas", "Constructie", "Productie", "Automation", "Renewable Energy"]
REGIO_OPTIES = ["Gelderland", "Overijssel", "Noord-Brabant", "Alle drie"]
FUNCTIES = ["Lasser", "Monteur", "Werkvoorbereider", "Constructeur", "Projectleider", "Service Engineer", "Anders"]

CPL_DEFAULTS = {
    "goed": 40,
    "pauseer": 60,
    "ctr_min": 0.8,
}

BUDGETS = {
    "klein": {"dagelijks": 15, "totaal": 450, "looptijd_dagen": 30},
    "medium": {"dagelijks": 30, "totaal": 900, "looptijd_dagen": 30},
    "groot": {"dagelijks": 60, "totaal": 1800, "looptijd_dagen": 30},
}


def vraag(label: str, default: str = "") -> str:
    prompt = f"{label}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    antwoord = input(prompt).strip()
    return antwoord if antwoord else default


def kies_uit(label: str, opties: list, default_idx: int = 0) -> str:
    print(f"\n{label}:")
    for i, o in enumerate(opties, 1):
        marker = " (standaard)" if i - 1 == default_idx else ""
        print(f"  {i}. {o}{marker}")
    keuze = input("Kies: ").strip()
    if keuze.isdigit() and 1 <= int(keuze) <= len(opties):
        return opties[int(keuze) - 1]
    return opties[default_idx]


def kies_meerdere(label: str, opties: list) -> list:
    print(f"\n{label} (kommagescheiden nummers, bijv. 1,3):")
    for i, o in enumerate(opties, 1):
        print(f"  {i}. {o}")
    keuze = input("Kies: ").strip()
    indices = [int(x.strip()) - 1 for x in keuze.split(",") if x.strip().isdigit()]
    return [opties[i] for i in indices if 0 <= i < len(opties)] or [opties[0]]


def build_input(campagne: str, dry_run: bool) -> dict:
    campagne_dir = CAMPAIGNS_DIR / campagne.replace(" ", "_")
    campagne_dir.mkdir(parents=True, exist_ok=True)

    # Laad bestaand onderzoek
    research_file = campagne_dir / "notebooklm-research.md"
    research_samenvatting = ""
    if research_file.exists():
        research_samenvatting = research_file.read_text()[:500]
        print(f"\nNotebookLM onderzoek gevonden ({len(research_file.read_text())} tekens).")

    print(f"\n=== Agent 03: Campaign Input Builder ===")
    print(f"Campagne: {campagne}\n")
    print("Beantwoord onderstaande vragen. Druk Enter voor standaardwaarde.\n")

    # Basis
    functie_keuze = kies_uit("Doelgroep functie", FUNCTIES)
    functie = vraag("Functietitel (exact)", functie_keuze) if functie_keuze == "Anders" else functie_keuze
    sector = kies_uit("Sector", SECTOREN)
    regio_keuze = kies_meerdere("Doelregio's", REGIO_OPTIES[:3])

    # Vacature
    print("\n--- Vacature details ---")
    vacature_titel = vraag("Vacature titel", f"{functie} gezocht")
    salaris_min = vraag("Salaris minimum (bruto/jaar)", "45000")
    salaris_max = vraag("Salaris maximum (bruto/jaar)", "65000")
    voordelen = vraag("Voordelen (kommagescheiden)", "lease auto, 27 vakantiedagen, pensioen")
    bedrijfsnaam = vraag("Opdrachtgever / klant naam", "Recruitin klant")
    bedrijf_type = vraag("Type bedrijf", "technisch installatiebedrijf")

    # Doelgroep
    print("\n--- Doelgroep ---")
    ervaringsjaren = vraag("Minimale ervaring (jaren)", "3")
    certificaten = vraag("Vereiste certificaten (kommagescheiden)", "VCA, rijbewijs B")
    pijn_punt = vraag("Grootste pijnpunt doelgroep", "geen doorgroeimogelijkheden bij huidige werkgever")
    motivatie = vraag("Switcmotivatie doelgroep", "beter salaris + uitdagender werk")

    # Budget & targeting
    print("\n--- Budget & targeting ---")
    budget_keuze = kies_uit("Budget preset", ["klein (€15/dag)", "medium (€30/dag)", "groot (€60/dag)"])
    budget_key = budget_keuze.split()[0]
    budget = BUDGETS.get(budget_key, BUDGETS["medium"])
    dagbudget = vraag("Dagelijks budget (€)", str(budget["dagelijks"]))
    cpl_max = vraag(f"Max CPL voordat je pauzeert (€)", str(CPL_DEFAULTS["pauseer"]))

    # Uniek
    print("\n--- Unique selling points ---")
    usp1 = vraag("USP 1 (schaarste/exclusiviteit)", f"Slechts {ervaringsjaren}+ ervaren {functie.lower()}s komen in aanmerking")
    usp2 = vraag("USP 2 (sociaal bewijs)", f"Al 40+ {functie.lower()}s succesvol geplaatst in {sector}")
    usp3 = vraag("USP 3 (urgentie)", "Vacature sluit zodra geschikte kandidaat gevonden is")

    data = {
        "campagne": campagne,
        "aangemaakt": datetime.now().isoformat(),
        "functie": functie,
        "sector": sector,
        "regio": regio_keuze,
        "vacature_titel": vacature_titel,
        "salaris_range": f"€{salaris_min} - €{salaris_max}",
        "voordelen": [v.strip() for v in voordelen.split(",")],
        "bedrijfsnaam": bedrijfsnaam,
        "bedrijf_type": bedrijf_type,
        "ervaringsjaren": ervaringsjaren,
        "certificaten": [c.strip() for c in certificaten.split(",")],
        "pijn_punt": pijn_punt,
        "motivatie": motivatie,
        "dagbudget": float(dagbudget),
        "cpl_max": float(cpl_max),
        "cpl_goed": CPL_DEFAULTS["goed"],
        "ctr_min": CPL_DEFAULTS["ctr_min"],
        "looptijd_dagen": budget["looptijd_dagen"],
        "usps": [usp1, usp2, usp3],
    }

    # Schrijf JSON
    json_file = campagne_dir / "campaign-input.json"
    json_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # Schrijf leesbare MD
    md_lines = [
        f"# Campaign Input — {campagne}",
        f"",
        f"**Aangemaakt:** {data['aangemaakt']}",
        f"",
        f"## Doelgroep",
        f"**Functie:** {functie}",
        f"**Sector:** {sector}",
        f"**Regio:** {', '.join(regio_keuze)}",
        f"**Ervaring:** {ervaringsjaren}+ jaar",
        f"**Certificaten:** {', '.join(data['certificaten'])}",
        f"",
        f"## Vacature",
        f"**Titel:** {vacature_titel}",
        f"**Salaris:** {data['salaris_range']} bruto/jaar",
        f"**Voordelen:** {', '.join(data['voordelen'])}",
        f"**Opdrachtgever:** {bedrijfsnaam} ({bedrijf_type})",
        f"",
        f"## Psychografie",
        f"**Pijnpunt:** {pijn_punt}",
        f"**Switcmotivatie:** {motivatie}",
        f"",
        f"## USPs",
        f"1. {usp1}",
        f"2. {usp2}",
        f"3. {usp3}",
        f"",
        f"## Budget & KPIs",
        f"**Dagbudget:** €{dagbudget}",
        f"**Max CPL:** €{cpl_max} (daarboven: pauzeer ad set)",
        f"**Goed CPL:** <€{CPL_DEFAULTS['goed']}",
        f"**Min CTR:** {CPL_DEFAULTS['ctr_min']}%",
        f"**Looptijd:** {budget['looptijd_dagen']} dagen",
        f"",
        f"## Ad Set Verdeling",
        f"- Prospecting (brede doelgroep): 60% budget",
        f"- Lookalike (vergelijkbaar publiek): 25% budget",
        f"- Retargeting (website bezoekers): 15% budget",
    ]

    md_file = campagne_dir / "campaign-input.md"
    md_file.write_text("\n".join(md_lines))

    print(f"\nInput opgeslagen:")
    print(f"  JSON: {json_file}")
    print(f"  MD:   {md_file}")

    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campagne", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = build_input(args.campagne, args.dry_run)

    print(f"\n=== Samenvatting ===")
    print(f"Functie:  {data['functie']}")
    print(f"Sector:   {data['sector']}")
    print(f"Regio:    {', '.join(data['regio'])}")
    print(f"Budget:   €{data['dagbudget']}/dag, max CPL €{data['cpl_max']}")
    print(f"\nAgent 03 klaar. Volgende: agent-04 (Meta API upload).")


if __name__ == "__main__":
    main()
