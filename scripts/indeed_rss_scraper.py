#!/opt/homebrew/bin/python3
"""
Indeed Vacatures RSS Scraper v1.0
===================================
Gebruikt Indeed's officiële RSS feed — GEEN Cloudflare, GEEN Playwright.
Direct HTTP requests naar nl.indeed.com/rss — altijd bereikbaar.

Output: CSV + SQLite in ~/recruitin/scraper-output/
"""

import csv
import json
import sqlite3
import logging
import hashlib
import time
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from typing import Dict, List, Optional
try:
    import requests
except ImportError:
    raise SystemExit("❌ Installeer requests: pip3 install requests --break-system-packages")

# ===== CONFIGURATIE =====
LOCATION = "Arnhem"
RADIUS = "30"
SEARCH_TERMS = [
    "projectleider",
    "werkvoorbereider",
    "monteur",
    "engineer technisch",
    "calculator",
]

OUTPUT_DIR = Path.home() / "Desktop" / "recruitin_scraper_output"
LOG_DIR   = Path("/tmp") / "recruitin_logs"
DB_PATH   = OUTPUT_DIR / "rss_vacancies.db"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===== LOGGING =====
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file  = LOG_DIR / f"indeed_rss_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ===== GLOBALS =====
VACANCIES: List[Dict] = []
STATS = {
    "total_found": 0,
    "total_unique": 0,
    "errors": 0,
    "by_term": {},
}

# ===== DATABASE =====
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            link_hash   TEXT UNIQUE NOT NULL,
            functie     TEXT NOT NULL,
            bedrijf     TEXT,
            plaats      TEXT,
            salaris     TEXT,
            gepost      TEXT,
            zoekterm    TEXT,
            link        TEXT NOT NULL,
            scraped_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            seen_before INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON vacancies(link_hash)")
    conn.commit()
    logger.info("✅ Database gereed")
    return conn


def _hash(link: str) -> str:
    return hashlib.sha256(link.encode()).hexdigest()


def is_duplicate(conn: sqlite3.Connection, link: str) -> bool:
    row = conn.execute(
        "SELECT id FROM vacancies WHERE link_hash = ? LIMIT 1", (_hash(link),)
    ).fetchone()
    return row is not None


def save_vacancy(conn: sqlite3.Connection, v: Dict) -> bool:
    """True = nieuw opgeslagen, False = duplicaat."""
    try:
        conn.execute("""
            INSERT INTO vacancies (link_hash, functie, bedrijf, plaats, salaris, gepost, zoekterm, link, scraped_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            _hash(v["link"]),
            v.get("functie", "N/A")[:200],
            v.get("bedrijf", "N/A")[:200],
            v.get("plaats", "N/A"),
            v.get("salaris", "Niet gegeven"),
            v.get("gepost", "N/A"),
            v.get("zoekterm", "N/A"),
            v["link"],
            v.get("scraped_at", datetime.now().isoformat()),
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


# ===== RSS SCRAPER =====
RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RSS reader; +https://recruitin.nl)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "nl-NL,nl;q=0.9",
}


def fetch_rss(search_term: str, start: int = 0) -> Optional[str]:
    """Haal één pagina RSS op. start=0,10,20... voor paginering."""
    url = (
        f"https://www.indeed.nl/rss"
        f"?q={quote_plus(search_term)}"
        f"&l={quote_plus(LOCATION)}"
        f"&radius={RADIUS}"
        f"&sort=date"
        f"&start={start}"
    )
    try:
        resp = requests.get(url, headers=RSS_HEADERS, timeout=20)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"   HTTP {resp.status_code} voor {url}")
        return None
    except requests.RequestException as e:
        logger.error(f"   Request fout: {e}")
        return None


def parse_rss(xml_text: str, search_term: str) -> List[Dict]:
    """Parse RSS XML naar lijst van vacature-dicts."""
    vacancies = []
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return vacancies

        items = channel.findall("item")
        for item in items:
            title    = (item.findtext("title") or "").strip()
            link     = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            desc     = (item.findtext("description") or "")

            if not title or not link:
                continue

            # Bedrijf extracten uit description (patroon: "<b>Company:</b> Acme BV")
            company_match = re.search(r'<b>Company</b>:?\s*([^<\n]+)', desc, re.IGNORECASE)
            company = company_match.group(1).strip() if company_match else "N/A"

            # Locatie extracten
            location_match = re.search(r'<b>Location</b>:?\s*([^<\n]+)', desc, re.IGNORECASE)
            location = location_match.group(1).strip() if location_match else LOCATION

            # Salaris extracten
            salary_match = re.search(r'(€[\d\.,][\d\.,\s\-]+(?:per|p\/|per\s+)?(?:uur|maand|jaar|hour|month|year)?)', desc, re.IGNORECASE)
            salary = salary_match.group(1).strip() if salary_match else "Niet gegeven"

            vacancies.append({
                "functie":    title[:200],
                "bedrijf":    company,
                "plaats":     location,
                "salaris":    salary,
                "gepost":     pub_date,
                "zoekterm":   search_term,
                "link":       link,
                "scraped_at": datetime.now().isoformat(),
            })
    except ET.ParseError as e:
        logger.error(f"   XML parse fout: {e}")
    return vacancies


def scrape_term(search_term: str, conn: sqlite3.Connection) -> None:
    logger.info(f"🔍 Scraping: '{search_term}'")
    count_new = 0
    count_dup = 0
    pages_scraped = 0
    max_pages = 10          # 10 × 10 = 100 vacatures per zoekterm
    start = 0

    while pages_scraped < max_pages:
        xml_text = fetch_rss(search_term, start=start)
        if not xml_text:
            logger.warning(f"   Geen RSS data op start={start}")
            break

        vacancies = parse_rss(xml_text, search_term)
        if not vacancies:
            logger.info(f"   Geen items meer op pagina {pages_scraped + 1}")
            break

        logger.info(f"   Pagina {pages_scraped + 1}: {len(vacancies)} items")

        for v in vacancies:
            STATS["total_found"] += 1
            if is_duplicate(conn, v["link"]):
                count_dup += 1
                continue
            if save_vacancy(conn, v):
                VACANCIES.append(v)
                STATS["total_unique"] += 1
                count_new += 1

        pages_scraped += 1
        start += 10

        # Beleefd wachten (0.8 - 2.5s) tussen pagina's
        if pages_scraped < max_pages and len(vacancies) == 10:
            delay = random.uniform(0.8, 2.5)
            time.sleep(delay)
        else:
            break  # Minder dan 10 items = laatste pagina

    STATS["by_term"][search_term] = {
        "new": count_new,
        "duplicates": count_dup,
        "pages": pages_scraped,
    }
    logger.info(f"   ✅ '{search_term}': {count_new} NIEUW | {count_dup} dup | {pages_scraped} pagina's")


# ===== EXPORT =====
def export_csv() -> Optional[str]:
    if not VACANCIES:
        logger.warning("Geen vacatures gevonden")
        return None
    try:
        path = OUTPUT_DIR / f"indeed_rss_{timestamp}.csv"
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


def export_json_stats() -> Optional[str]:
    try:
        path = OUTPUT_DIR / f"indeed_rss_stats_{timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                **STATS,
                "timestamp": timestamp,
                "location": LOCATION,
                "radius": RADIUS,
                "search_terms": SEARCH_TERMS,
                "log": str(log_file),
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Stats: {path}")
        return str(path)
    except IOError as e:
        logger.error(f"JSON fout: {e}")
        return None


# ===== MAIN =====
def main():
    logger.info("=" * 65)
    logger.info(" Indeed RSS Scraper v1.0  —  Cloudflare-proof")
    logger.info("=" * 65)
    logger.info(f" Locatie   : {LOCATION} ({RADIUS}km)")
    logger.info(f" Zoektermen: {', '.join(SEARCH_TERMS)}")
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

        # Beleefd wachten tussen zoektermen
        if idx < len(SEARCH_TERMS):
            wait = random.uniform(2, 5)
            logger.info(f"   ⏳ {wait:.1f}s wachten...")
            time.sleep(wait)

    conn.close()

    csv_path  = export_csv()
    json_path = export_json_stats()

    logger.info("\n" + "=" * 65)
    logger.info(" RESULTATEN")
    logger.info("=" * 65)
    logger.info(f" Totaal gevonden : {STATS['total_found']}")
    logger.info(f" Totaal nieuw    : {STATS['total_unique']}")
    logger.info(f" Fouten          : {STATS['errors']}")
    for term, s in STATS["by_term"].items():
        logger.info(f"   {term:<25} {s['new']:>3} nieuw  {s['duplicates']:>3} dup  {s['pages']} pag.")
    logger.info(f"\n CSV  : {csv_path or 'N/A'}")
    logger.info(f" JSON : {json_path or 'N/A'}")
    logger.info(f" Log  : {log_file}")
    logger.info("=" * 65)

    result = {
        "status": "success" if STATS["errors"] == 0 else "partial_error",
        "csv_file": csv_path,
        "json_file": json_path,
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
        print(json.dumps({"status": "error", "error": str(e), "timestamp": timestamp}, indent=2))
