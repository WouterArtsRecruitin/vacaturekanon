#!/usr/bin/env python3
"""
Agent 05 — Monitor Update
Voegt nieuwe campagne toe aan kt-daily-monitor.py en genereert monitoring config.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CAMPAIGNS_DIR = BASE_DIR / "campaigns"

# Bekende locaties voor kt-daily-monitor.py
MONITOR_SEARCH_PATHS = [
    Path.home() / "recruitin" / "kt-daily-monitor.py",
    Path.home() / "recruitin" / "meta-campaigns" / "kt-daily-monitor.py",
    Path.home() / "DATA" / "Exports" / "jobdigger" / "jobdigger-automation" / "kt-daily-monitor.py",
]


def find_monitor_script() -> Path | None:
    for p in MONITOR_SEARCH_PATHS:
        if p.exists():
            return p
    return None


def load_campaign_report(campagne: str) -> dict:
    campagne_dir = CAMPAIGNS_DIR / campagne.replace(" ", "_")
    report_file = campagne_dir / "campaign-report.json"
    if not report_file.exists():
        print(f"[FOUT] campaign-report.json niet gevonden: {report_file}")
        print("Voer eerst Agent 04 uit.")
        sys.exit(1)
    return json.loads(report_file.read_text())


def build_monitor_entry(report: dict, input_data: dict) -> dict:
    return {
        "naam": report["campagne"],
        "campaign_id": report["campaign_id"],
        "ad_sets": list(report["ad_sets"].values()),
        "cpl_goed": report["cpl_goed"],
        "cpl_max": report["cpl_max"],
        "ctr_min": report["ctr_min"],
        "dagbudget": report["dagbudget"],
        "status": "PAUSED",
        "aangemaakt": report["aangemaakt"],
        "sector": input_data.get("sector", ""),
        "functie": input_data.get("functie", ""),
        "regio": input_data.get("regio", []),
        "jotform_url": report.get("jotform_url", ""),
    }


def patch_monitor_script(monitor_path: Path, entry: dict, dry_run: bool) -> bool:
    """Voeg campagne toe aan CAMPAIGNS lijst in monitor script."""
    content = monitor_path.read_text()

    # Zoek CAMPAIGNS = [ ... ] blok
    pattern = r"(CAMPAIGNS\s*=\s*\[)(.*?)(\])"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"[WARN] Geen CAMPAIGNS lijst gevonden in {monitor_path}")
        return False

    # Check of campagne al bestaat
    if entry["campaign_id"] in content:
        print(f"Campagne {entry['campaign_id']} al aanwezig in monitor script.")
        return True

    new_entry = f"\n    {json.dumps(entry, ensure_ascii=False)},"
    new_campaigns = match.group(1) + match.group(2) + new_entry + "\n" + match.group(3)
    new_content = content[:match.start()] + new_campaigns + content[match.end():]

    if dry_run:
        print(f"[DRY-RUN] Zou toevoegen aan {monitor_path}:")
        print(f"  {json.dumps(entry, indent=4, ensure_ascii=False)}")
        return True

    monitor_path.write_text(new_content)
    print(f"Toegevoegd aan {monitor_path}")
    return True


def generate_standalone_monitor_config(campagne_dir: Path, entry: dict):
    """Genereer losse monitor config als fallback."""
    config_file = campagne_dir / "monitor-config.json"
    config = {
        "versie": "1.0",
        "aangemaakt": datetime.now().isoformat(),
        "campagnes": [entry],
        "instructie": (
            "Voeg dit blok toe aan CAMPAIGNS in kt-daily-monitor.py, "
            "of gebruik deze file als standalone monitor config."
        ),
    }
    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    print(f"Monitor config opgeslagen: {config_file}")
    return config_file


def print_monitor_summary(entry: dict):
    print(f"\n=== Monitor Configuratie ===")
    print(f"Naam:         {entry['naam']}")
    print(f"Campaign ID:  {entry['campaign_id']}")
    print(f"Sector:       {entry['sector']} — {entry['functie']}")
    print(f"Regio:        {', '.join(entry['regio'])}")
    print(f"Budget:       €{entry['dagbudget']}/dag")
    print(f"KPIs:         CPL goed <€{entry['cpl_goed']} | pauzeer >€{entry['cpl_max']} | CTR min {entry['ctr_min']}%")
    print(f"Status:       {entry['status']}")
    print(f"\nAd sets ({len(entry['ad_sets'])}):")
    for ad_set_id in entry["ad_sets"]:
        print(f"  - {ad_set_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campagne", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--monitor-path", help="Pad naar kt-daily-monitor.py")
    args = parser.parse_args()

    campagne = args.campagne
    campagne_dir = CAMPAIGNS_DIR / campagne.replace(" ", "_")

    print(f"\n=== Agent 05: Monitor Update ===")
    print(f"Campagne: {campagne}")

    # Laad rapport en input
    report = load_campaign_report(campagne)
    input_file = campagne_dir / "campaign-input.json"
    input_data = json.loads(input_file.read_text()) if input_file.exists() else {}

    entry = build_monitor_entry(report, input_data)
    print_monitor_summary(entry)

    # Zoek monitor script
    if args.monitor_path:
        monitor_path = Path(args.monitor_path)
    else:
        monitor_path = find_monitor_script()

    if monitor_path and monitor_path.exists():
        print(f"\nMonitor script gevonden: {monitor_path}")
        succes = patch_monitor_script(monitor_path, entry, args.dry_run)
        if succes:
            print("Monitor script bijgewerkt.")
    else:
        print(f"\n[WARN] kt-daily-monitor.py niet gevonden.")
        print(f"Gezocht in:")
        for p in MONITOR_SEARCH_PATHS:
            print(f"  {p}")

    # Altijd losse config opslaan
    config_file = generate_standalone_monitor_config(campagne_dir, entry)

    # Afsluitende instructies
    print(f"\n=== Volgende stappen ===")
    print(f"1. Review campagne in Meta Ads Manager:")
    print(f"   https://www.facebook.com/adsmanager/manage/campaigns?act={report.get('account_id', '')}")
    print(f"")
    print(f"2. Activeer campagne handmatig na review (nu PAUSED).")
    print(f"")
    print(f"3. Voeg monitor toe aan dagelijkse run:")
    if monitor_path:
        print(f"   python3 {monitor_path} --campagne '{campagne}'")
    else:
        print(f"   Configureer kt-daily-monitor.py met: {config_file}")
    print(f"")
    print(f"4. KPI targets:")
    print(f"   CPL goed: <€{entry['cpl_goed']} | Pauzeer: >€{entry['cpl_max']} | CTR min: {entry['ctr_min']}%")

    print(f"\nAgent 05 klaar. Pipeline volledig afgerond!")


if __name__ == "__main__":
    main()
