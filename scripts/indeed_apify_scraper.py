#!/opt/homebrew/bin/python3
"""
Indeed Vacatures via Apify v1.0
================================
Gebruikt Apify's managed Indeed Scraper actor.
Geen Cloudflare issues — Apify handelt dit intern af.

Prijs: ~$0.50 per 1000 vacatures (pay-per-use)
Actor: misceres/indeed-scraper

Setup:
  1. Maak account op https://apify.com (gratis tier: $5 credit/mnd)
  2. Kopieer je API token van: https://console.apify.com/account/integrations
  3. Zet APIFY_TOKEN in ~/recruitin/.env

Output: CSV + SQLite → ~/Desktop/recruitin_scraper_output/
"""

import csv
import json
import sqlite3
import logging
import hashlib
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    sys.exit("❌ Run: pip3 install requests --break-system-packages")

try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "recruitin" / ".env")
except ImportError:
    pass

import os

# ===== APIFY CONFIG =====
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
ACTOR_ID    = "misceres~indeed-scraper"   # Meest gebruikte Indeed actor op Apify
APIFY_BASE  = "https://api.apify.com/v2"

# ===== ZOEKCONFIG =====
LOCATION    = "Arnhem, Netherlands"
RADIUS_KM   = 30
MAX_RESULTS = 50   # Per zoekterm (verhoog naar 200 voor volledige sweep)
SEARCH_TERMS = [
    "projectleider",
    "werkvoorbereider",
    "monteur",
    "engineer technisch",
    "calculator",
]

# ===== PADEN =====
OUTPUT_DIR = Path.home() / "Desktop" / "recruitin_scraper_output"
LOG_DIR    = Path("/tmp") / "recruitin_logs"
DB_PATH    = OUTPUT_DIR / "apify_vacancies.db"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===== LOGGING =====
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file  = LOG_DIR / f"indeed_apify_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ===== GLOBALS =====
VACANCIES: List[Dict] = []
STATS = {"total_found": 0, "total_unique": 0, "errors": 0, "by_term": {}}


# ===== DATABASE =====
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            link_hash   TEXT UNIQUE NOT NULL,
            functie     TEXT,
            bedrijf     TEXT,
            plaats      TEXT,
            salaris     TEXT,
            gepost      TEXT,
            zoekterm    TEXT,
            link        TEXT NOT NULL,
            scraped_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            seen_before INTEGER DEFAULT 0,
            apify_run   TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON vacancies(link_hash)")
    conn.commit()
    logger.info("✅ Database gereed")
    return conn


def _hash(link: str) -> str:
    return hashlib.sha256(link.encode()).hexdigest()


def is_duplicate(conn: sqlite3.Connection, link: str) -> bool:
    return conn.execute(
        "SELECT id FROM vacancies WHERE link_hash = ? LIMIT 1", (_hash(link),)
    ).fetchone() is not None


def save_vacancy(conn: sqlite3.Connection, v: Dict, run_id: str) -> bool:
    try:
        conn.execute("""
            INSERT INTO vacancies
              (link_hash, functie, bedrijf, plaats, salaris, gepost, zoekterm, link, scraped_at, apify_run)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            _hash(v["link"]),
            v.get("functie", "N/A")[:200],
            v.get("bedrijf", "N/A")[:200],
            v.get("plaats", LOCATION),
            v.get("salaris", "Niet gegeven"),
            v.get("gepost", "N/A"),
            v.get("zoekterm", "N/A"),
            v["link"],
            v.get("scraped_at", datetime.now().isoformat()),
            run_id,
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.execute(
            "UPDATE vacancies SET seen_before = 1 WHERE link_hash = ?", (_hash(v["link"]),)
        )
        conn.commit()
        return False
    except sqlite3.Error as e:
        logger.error(f"DB fout: {e}")
        return False


# ===== APIFY API =====
def _headers() -> Dict:
    return {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json",
    }


def run_actor(search_term: str) -> Optional[str]:
    """
    Start de Apify Indeed scraper voor één zoekterm.
    Returnt run_id of None bij fout.
    """
    payload = {
        "position": search_term,
        "location": LOCATION,
        "maxItems": MAX_RESULTS,
        "country": "NL",
        "sort": "date",          # Meest recent eerst
        "parseCompanyDetails": False,
    }

    url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs"
    try:
        r = requests.post(url, headers=_headers(), json=payload, timeout=30)
        if r.status_code in (200, 201):
            run_id = r.json()["data"]["id"]
            logger.info(f"   🚀 Actor gestart | run_id: {run_id}")
            return run_id
        else:
            logger.error(f"   Actor start fout: HTTP {r.status_code} — {r.text[:200]}")
            return None
    except requests.RequestException as e:
        logger.error(f"   Request fout: {e}")
        return None


def wait_for_run(run_id: str, timeout_sec: int = 300) -> bool:
    """Wacht tot de Apify run klaar is. Max 5 minuten."""
    url = f"{APIFY_BASE}/actor-runs/{run_id}"
    start = time.time()
    poll_interval = 5

    while time.time() - start < timeout_sec:
        try:
            r = requests.get(url, headers=_headers(), timeout=15)
            if r.status_code == 200:
                status = r.json()["data"]["status"]
                if status == "SUCCEEDED":
                    logger.info(f"   ✅ Run voltooid (status: {status})")
                    return True
                elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    logger.error(f"   ❌ Run mislukt: {status}")
                    return False
                else:
                    elapsed = int(time.time() - start)
                    logger.info(f"   ⏳ Run status: {status} ({elapsed}s)...")
        except requests.RequestException as e:
            logger.warning(f"   Poll fout: {e}")

        time.sleep(poll_interval)
        poll_interval = min(poll_interval + 3, 20)  # Backoff

    logger.error(f"   Timeout na {timeout_sec}s")
    return False


def fetch_results(run_id: str) -> List[Dict]:
    """Haal items op uit de dataset van een voltooide run."""
    url = f"{APIFY_BASE}/actor-runs/{run_id}/dataset/items"
    try:
        r = requests.get(
            url,
            headers=_headers(),
            params={"format": "json", "clean": "true"},
            timeout=60,
        )
        if r.status_code == 200:
            items = r.json()
            logger.info(f"   📦 {len(items)} items opgehaald uit dataset")
            return items
        else:
            logger.error(f"   Dataset fout: HTTP {r.status_code}")
            return []
    except requests.RequestException as e:
        logger.error(f"   Fetch fout: {e}")
        return []


def normalize_vacancy(item: Dict, search_term: str) -> Optional[Dict]:
    """
    Zet Apify resultaat om naar ons standaard format.
    Apify's indeed-scraper geeft: positionName, company, location, salary, postedAt, url
    """
    link = item.get("url") or item.get("jobUrl") or item.get("link", "")
    if not link:
        return None

    # Salaris samenvoegen als object
    salary = item.get("salary") or item.get("salaryRange", "")
    if isinstance(salary, dict):
        low  = salary.get("from", "")
        high = salary.get("to", "")
        per  = salary.get("per", "")
        salary_str = f"€{low} - €{high} {per}".strip(" -") if low else "Niet gegeven"
    else:
        salary_str = str(salary) if salary else "Niet gegeven"

    return {
        "functie":    (item.get("positionName") or item.get("title") or "N/A")[:200],
        "bedrijf":    (item.get("company") or item.get("companyName") or "N/A")[:200],
        "plaats":     item.get("location") or LOCATION,
        "salaris":    salary_str,
        "gepost":     str(item.get("postedAt") or item.get("publishedAt") or "N/A"),
        "zoekterm":   search_term,
        "link":       link,
        "scraped_at": datetime.now().isoformat(),
    }


# ===== SCRAPE PER TERM =====
def scrape_term(search_term: str, conn: sqlite3.Connection) -> None:
    logger.info(f"🔍 Zoekterm: '{search_term}'")
    count_new = 0
    count_dup = 0

    # 1. Start actor
    run_id = run_actor(search_term)
    if not run_id:
        STATS["errors"] += 1
        STATS["by_term"][search_term] = {"new": 0, "duplicates": 0, "error": True}
        return

    # 2. Wacht op voltooiing
    success = wait_for_run(run_id)
    if not success:
        STATS["errors"] += 1
        STATS["by_term"][search_term] = {"new": 0, "duplicates": 0, "error": True}
        return

    # 3. Haal resultaten op
    items = fetch_results(run_id)

    # 4. Verwerk
    for item in items:
        vacancy = normalize_vacancy(item, search_term)
        if not vacancy:
            continue

        STATS["total_found"] += 1
        if is_duplicate(conn, vacancy["link"]):
            count_dup += 1
            continue

        if save_vacancy(conn, vacancy, run_id):
            VACANCIES.append(vacancy)
            STATS["total_unique"] += 1
            count_new += 1

    STATS["by_term"][search_term] = {
        "new": count_new,
        "duplicates": count_dup,
        "run_id": run_id,
    }
    logger.info(
        f"   ✅ '{search_term}': {count_new} NIEUW | {count_dup} dup | run: {run_id}"
    )


# ===== EXPORT =====
def export_csv() -> Optional[str]:
    if not VACANCIES:
        logger.warning("Geen vacatures om te exporteren")
        return None
    try:
        path = OUTPUT_DIR / f"indeed_apify_{timestamp}.csv"
        fields = ["functie", "bedrijf", "plaats", "salaris", "gepost", "zoekterm", "link", "scraped_at"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(VACANCIES)
        logger.info(f"✅ CSV: {path} ({len(VACANCIES)} rijen)")
        return str(path)
    except IOError as e:
        logger.error(f"CSV fout: {e}")
        return None


def export_stats() -> Optional[str]:
    try:
        path = OUTPUT_DIR / f"indeed_apify_stats_{timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                **STATS,
                "timestamp": timestamp,
                "location": LOCATION,
                "radius_km": RADIUS_KM,
                "search_terms": SEARCH_TERMS,
                "actor": ACTOR_ID,
                "log": str(log_file),
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Stats: {path}")
        return str(path)
    except IOError as e:
        logger.error(f"Stats fout: {e}")
        return None


# ===== MAIN =====
def main():
    logger.info("=" * 65)
    logger.info(" Indeed via Apify v1.0  —  Cloudflare-proof")
    logger.info("=" * 65)

    # Token check
    if not APIFY_TOKEN:
        logger.error("""
❌ APIFY_TOKEN niet gevonden!

Stappen:
  1. Ga naar https://apify.com — maak gratis account
     (gratis tier = $5 credit/mnd, genoeg voor honderden runs)
  2. Ga naar https://console.apify.com/account/integrations
  3. Kopieer je 'Personal API token'
  4. Voeg toe aan ~/recruitin/.env:
        APIFY_TOKEN=apify_api_xxxxxxxxxxxx
  5. Herstart dit script
        """)
        sys.exit(1)

    logger.info(f" Actor     : {ACTOR_ID}")
    logger.info(f" Locatie   : {LOCATION} ({RADIUS_KM}km)")
    logger.info(f" Zoektermen: {', '.join(SEARCH_TERMS)}")
    logger.info(f" Max/term  : {MAX_RESULTS} vacatures")
    logger.info(f" Output    : {OUTPUT_DIR}")
    logger.info("=" * 65)

    conn = init_db()

    for idx, term in enumerate(SEARCH_TERMS, 1):
        logger.info(f"\n[{idx}/{len(SEARCH_TERMS)}] {term}")
        try:
            scrape_term(term, conn)
        except Exception as e:
            logger.error(f"Fout bij '{term}': {e}")
            STATS["errors"] += 1

    conn.close()

    csv_path   = export_csv()
    stats_path = export_stats()

    logger.info("\n" + "=" * 65)
    logger.info(" RESULTATEN")
    logger.info("=" * 65)
    logger.info(f" Totaal gevonden : {STATS['total_found']}")
    logger.info(f" Totaal nieuw    : {STATS['total_unique']}")
    logger.info(f" Fouten          : {STATS['errors']}")
    logger.info("")
    for term, s in STATS["by_term"].items():
        err = " ❌ ERROR" if s.get("error") else ""
        logger.info(f"   {term:<25} {s['new']:>3} nieuw  {s['duplicates']:>3} dup{err}")
    logger.info(f"\n CSV   : {csv_path or 'N/A'}")
    logger.info(f" Stats : {stats_path or 'N/A'}")
    logger.info(f" Log   : {log_file}")
    logger.info("=" * 65)

    result = {
        "status": "success" if STATS["errors"] == 0 else "partial_error",
        "csv_file": csv_path,
        "stats_file": stats_path,
        "log_file": str(log_file),
        "total_found": STATS["total_found"],
        "total_new": STATS["total_unique"],
        "errors": STATS["errors"],
        "timestamp": timestamp,
    }
    print("\n" + "=" * 65)
    print("JSON OUTPUT VOOR ZAPIER:")
    print("=" * 65)
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Gestopt door gebruiker")
    except Exception as e:
        logger.error(f"Fatale fout: {e}")
        print(json.dumps({"status": "error", "error": str(e), "timestamp": timestamp}))
