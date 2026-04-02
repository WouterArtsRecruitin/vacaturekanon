#!/usr/bin/env python3
"""
Master Agent — Meta Ads Campaign Orchestrator
Orkestreert 5 sub-agents: NotebookLM → Visual Validator → Input Builder → Meta Campaign → Monitor
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)

AGENTS = [
    (1, "agent-01-notebooklm.py",      "NotebookLM prompts + browser"),
    (2, "agent-02-visual-validator.py", "Visual validatie (4x PNG 1080px)"),
    (3, "agent-03-input-builder.py",    "Campaign input builder"),
    (4, "agent-04-meta-campaign.py",    "Meta Marketing API upload"),
    (5, "agent-05-monitor-update.py",   "Monitor toevoegen aan kt-daily"),
]


def state_file(campagne: str) -> Path:
    return STATE_DIR / f"{campagne.replace(' ', '_')}.json"


def load_state(campagne: str) -> dict:
    f = state_file(campagne)
    if f.exists():
        return json.loads(f.read_text())
    return {"campagne": campagne, "completed": [], "started": None, "updated": None}


def save_state(campagne: str, state: dict):
    state["updated"] = datetime.now().isoformat()
    state_file(campagne).write_text(json.dumps(state, indent=2))


def print_status(campagne: str, state: dict):
    completed = state.get("completed", [])
    print(f"\n=== Pipeline: {campagne} ===")
    print(f"Gestart: {state.get('started', 'nog niet')}")
    print(f"Bijgewerkt: {state.get('updated', '-')}\n")
    for num, script, label in AGENTS:
        status = "[OK]" if num in completed else "[ ]"
        print(f"  {status} Agent {num}: {label}")
    print()


def run_agent(num: int, script: str, campagne: str, dry_run: bool) -> bool:
    agent_path = BASE_DIR / "agents" / script
    if not agent_path.exists():
        print(f"[FOUT] Agent niet gevonden: {agent_path}")
        return False

    cmd = [sys.executable, str(agent_path), "--campagne", campagne]
    if dry_run:
        cmd.append("--dry-run")

    print(f"\n--- Agent {num}: {script} ---")
    if dry_run:
        print(f"[DRY-RUN] Zou uitvoeren: {' '.join(cmd)}")
        return True

    result = subprocess.run(cmd)
    return result.returncode == 0


def choose_campagne() -> str:
    state_files = list(STATE_DIR.glob("*.json"))
    existing = []
    for f in state_files:
        try:
            data = json.loads(f.read_text())
            existing.append(data.get("campagne", f.stem))
        except Exception:
            pass

    print("\n=== Meta Ads Campaign Orchestrator ===")
    if existing:
        print("\nBestaande campagnes:")
        for i, name in enumerate(existing, 1):
            print(f"  {i}. {name}")
        print(f"  {len(existing)+1}. Nieuwe campagne aanmaken")
        keuze = input("\nKies nummer of typ naam: ").strip()
        if keuze.isdigit():
            idx = int(keuze) - 1
            if 0 <= idx < len(existing):
                return existing[idx]
    naam = input("Campagne naam (bijv. 'Welders-Gelderland-Q2'): ").strip()
    if not naam:
        naam = f"campagne-{datetime.now().strftime('%Y%m%d-%H%M')}"
    return naam


def main():
    parser = argparse.ArgumentParser(description="Meta Ads Campaign Master Agent")
    parser.add_argument("--campagne", "-c", help="Campagne naam")
    parser.add_argument("--dry-run", action="store_true", help="Simuleer zonder API calls")
    parser.add_argument("--status", action="store_true", help="Toon pipeline status")
    parser.add_argument("--from-agent", type=int, metavar="N", help="Herstart vanaf agent N (1-5)")
    parser.add_argument("--reset", action="store_true", help="Reset pipeline state")
    args = parser.parse_args()

    # --status zonder --campagne toont alle campagnes
    if args.status and not args.campagne:
        state_files = list(STATE_DIR.glob("*.json"))
        if not state_files:
            print("\nGeen campagnes gevonden. Start met:\n  python3 master-agent.py --campagne 'Naam'")
            return
        for f in sorted(state_files):
            try:
                s = json.loads(f.read_text())
                print_status(s.get("campagne", f.stem), s)
            except Exception:
                pass
        return

    campagne = args.campagne or choose_campagne()
    state = load_state(campagne)

    if args.reset:
        state = {"campagne": campagne, "completed": [], "started": None, "updated": None}
        save_state(campagne, state)
        print(f"State gereset voor: {campagne}")
        return

    if args.status:
        print_status(campagne, state)
        return

    if not state.get("started"):
        state["started"] = datetime.now().isoformat()

    start_from = args.from_agent or 1
    completed = set(state.get("completed", []))

    print_status(campagne, state)

    agents_to_run = [(n, s, l) for n, s, l in AGENTS if n >= start_from and n not in completed]

    if not agents_to_run:
        print("Alle agents al voltooid. Gebruik --reset om opnieuw te starten.")
        return

    if args.from_agent:
        print(f"Hervatten vanaf agent {args.from_agent}...")
    else:
        bevestig = input(f"Start pipeline voor '{campagne}'? [j/n]: ").strip().lower()
        if bevestig != "j":
            print("Geannuleerd.")
            return

    for num, script, label in agents_to_run:
        print(f"\n[{num}/5] {label}")
        succes = run_agent(num, script, campagne, args.dry_run)

        if succes:
            completed.add(num)
            state["completed"] = sorted(completed)
            save_state(campagne, state)
            print(f"Agent {num} voltooid.")
        else:
            print(f"\n[STOP] Agent {num} mislukt.")
            print(f"Hervat met: python3 master-agent.py --campagne '{campagne}' --from-agent {num}")
            save_state(campagne, state)
            sys.exit(1)

    print(f"\n=== Pipeline voltooid voor: {campagne} ===")
    print_status(campagne, state)


if __name__ == "__main__":
    main()
