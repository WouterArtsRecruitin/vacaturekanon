#!/usr/bin/env python3
"""
Install script — Meta Campaigns Pipeline
Checkt dependencies, env vars en maakt directory structuur aan.
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

REQUIRED_DIRS = [
    "agents", "skills", "campaigns", "state", "assets", "templates",
]

REQUIRED_PACKAGES = [
    "anthropic",
    "requests",
]

REQUIRED_ENV_VARS = [
    "META_ACCESS_TOKEN",
    "META_ACCOUNT_ID",
    "META_PIXEL_ID",
    "JOTFORM_FORM_ID",
    "ANTHROPIC_API_KEY",
]

AGENTS = [
    "agents/agent-01-notebooklm.py",
    "agents/agent-02-visual-validator.py",
    "agents/agent-03-input-builder.py",
    "agents/agent-04-meta-campaign.py",
    "agents/agent-05-monitor-update.py",
]


def check(label: str, ok: bool, fix: str = ""):
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}")
    if not ok and fix:
        print(f"         Fix: {fix}")
    return ok


def main():
    print("\n=== Meta Campaigns Pipeline — Install Check ===\n")
    all_ok = True

    # Directories
    print("Directories:")
    for d in REQUIRED_DIRS:
        path = BASE_DIR / d
        path.mkdir(parents=True, exist_ok=True)
        ok = check(d, path.exists())
        all_ok = all_ok and ok

    # Python packages
    print("\nPython packages:")
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            ok = True
        except ImportError:
            ok = False
        check(pkg, ok, f"pip install {pkg}")
        if not ok:
            all_ok = False
            try:
                print(f"         Installeren...")
                subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=True)
                print(f"         Geinstalleerd: {pkg}")
            except subprocess.CalledProcessError:
                print(f"         Installatie mislukt: pip install {pkg}")

    # Agent scripts
    print("\nAgent scripts:")
    for agent in AGENTS:
        path = BASE_DIR / agent
        ok = check(agent, path.exists(), f"Ontbreekt: {path}")
        all_ok = all_ok and ok
        if path.exists():
            path.chmod(0o755)

    # Env vars
    print("\nEnvironment variables:")
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        val = os.environ.get(var, "")
        ok = bool(val)
        check(var, ok, f"Voeg toe aan ~/.zshrc: export {var}='...'")
        if not ok:
            missing_vars.append(var)
        all_ok = all_ok and ok

    # Maak master agent executable
    master = BASE_DIR / "master-agent.py"
    if master.exists():
        master.chmod(0o755)

    print(f"\n{'='*40}")
    if all_ok:
        print("Installatie OK. Klaar om te starten:\n")
        print("  python3 master-agent.py --status")
        print("  python3 master-agent.py")
        print("  python3 master-agent.py --campagne 'Welders-Gelderland-Q2' --dry-run")
    else:
        print("Installatie heeft problemen. Los bovenstaande FAIL items op.\n")
        if missing_vars:
            print("Ontbrekende env vars — voeg toe aan ~/.zshrc:")
            for var in missing_vars:
                print(f"  export {var}='JOUW_WAARDE_HIER'")
            print("  source ~/.zshrc")
        sys.exit(1)


if __name__ == "__main__":
    main()
