#!/usr/bin/env python3
"""
Agent 01 — NotebookLM Prompt Generator
Genereert 5 onderzoeksprompts op basis van sector/regio en opent browser.
"""

import argparse
import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CAMPAIGNS_DIR = BASE_DIR / "campaigns"

SECTOREN = ["Oil & Gas", "Constructie", "Productie", "Automation", "Renewable Energy"]
REGIO = ["Gelderland", "Overijssel", "Noord-Brabant"]

PROMPT_TEMPLATES = [
    "Wat zijn de 3 grootste uitdagingen bij het werven van {functie} in de {sector} sector in {regio} in 2025?",
    "Wat zijn de meest gehoorde bezwaren van {functie} professionals bij een nieuwe baan in {sector}?",
    "Welke specifieke vakjargon, tools en certificaten gebruiken {functie} professionals in {sector} dagelijks?",
    "Wat motiveert {functie} in {sector} om van werkgever te wisselen? Wat zijn push- en pull-factoren?",
    "Beschrijf de ideale werkgever vanuit het perspectief van een ervaren {functie} in de {sector} industrie in Nederland.",
]


def load_campaign_config(campagne: str) -> dict:
    campagne_dir = CAMPAIGNS_DIR / campagne.replace(" ", "_")
    config_file = campagne_dir / "campaign-input.md"
    if config_file.exists():
        # Probeer functie + sector uit bestaand bestand te halen
        text = config_file.read_text()
        config = {"raw": text}
        for line in text.splitlines():
            if line.startswith("**Functie"):
                config["functie"] = line.split(":", 1)[-1].strip().strip("*").strip()
            if line.startswith("**Sector"):
                config["sector"] = line.split(":", 1)[-1].strip().strip("*").strip()
            if line.startswith("**Regio"):
                config["regio"] = line.split(":", 1)[-1].strip().strip("*").strip()
        return config
    return {}


def choose_from_list(label: str, opties: list) -> str:
    print(f"\n{label}:")
    for i, o in enumerate(opties, 1):
        print(f"  {i}. {o}")
    keuze = input(f"Kies nummer of typ zelf: ").strip()
    if keuze.isdigit() and 1 <= int(keuze) <= len(opties):
        return opties[int(keuze) - 1]
    return keuze


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campagne", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    campagne = args.campagne
    campagne_dir = CAMPAIGNS_DIR / campagne.replace(" ", "_")
    campagne_dir.mkdir(parents=True, exist_ok=True)

    output_file = campagne_dir / "notebooklm-prompts.md"

    print(f"\n=== Agent 01: NotebookLM Marktonderzoek ===")
    print(f"Campagne: {campagne}")

    # Haal info op of vraag interactief
    config = load_campaign_config(campagne)
    functie = config.get("functie") or input("\nDoelgroep / functie (bijv. 'lasser', 'monteur'): ").strip()
    sector = config.get("sector") or choose_from_list("Sector", SECTOREN)
    regio = config.get("regio") or choose_from_list("Regio", REGIO)

    prompts = [t.format(functie=functie, sector=sector, regio=regio) for t in PROMPT_TEMPLATES]

    # Genereer markdown output
    lines = [
        f"# NotebookLM Marktonderzoek — {campagne}",
        f"",
        f"**Functie:** {functie}",
        f"**Sector:** {sector}",
        f"**Regio:** {regio}",
        f"",
        f"## Stap 1: Bronnen toevoegen in NotebookLM",
        f"",
        f"Voeg deze bronnen toe:",
        f"- LinkedIn-vacatures voor {functie} in {sector} (zoek via LinkedIn Jobs)",
        f"- Brancherapporten {sector} (bijv. FME, Techniek Nederland, Nogepa)",
        f"- Reddit/forum threads: r/Netherlands arbeidsmarkt",
        f"- CAO {sector} samenvatting",
        f"- Concurrentie vacatureteksten (5-10 stuks)",
        f"",
        f"## Stap 2: Prompts (voer 1 voor 1 in)",
        f"",
    ]
    for i, prompt in enumerate(prompts, 1):
        lines.append(f"### Prompt {i}")
        lines.append(f"```")
        lines.append(prompt)
        lines.append(f"```")
        lines.append(f"")

    lines += [
        f"## Stap 3: Sla output op",
        f"",
        f"Kopieer de antwoorden naar:",
        f"`campaigns/{campagne.replace(' ', '_')}/notebooklm-research.md`",
        f"",
        f"Gebruik dit als input voor Agent 03 (campaign-input builder).",
    ]

    content = "\n".join(lines)
    output_file.write_text(content)
    print(f"\nPrompts opgeslagen: {output_file}")
    print("\n--- Prompts preview ---")
    for i, p in enumerate(prompts, 1):
        print(f"\n[{i}] {p}")

    if not args.dry_run:
        antwoord = input("\nBrowser openen naar NotebookLM? [j/n]: ").strip().lower()
        if antwoord == "j":
            webbrowser.open("https://notebooklm.google.com")
            print("Browser geopend. Voer de prompts handmatig in.")
    else:
        print("\n[DRY-RUN] Browser niet geopend.")

    print(f"\nAgent 01 klaar. Volgende stap: agent-02 (visual validator).")


if __name__ == "__main__":
    main()
