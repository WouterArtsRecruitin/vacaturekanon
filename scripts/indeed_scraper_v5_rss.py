#!/opt/homebrew/bin/python3
"""
Indeed Vacatures Scraper v5.0 - RSS FEED
Simple & reliable RSS-based scraper:
  - No Cloudflare blocking
  - No browser automation
  - Instant results
  - Minimal dependencies (feedparser)
  - SQLite deduplication & history
  - CSV + JSON export
"""

import csv
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import feedparser
import hashlib
from html.parser import HTMLParser
import requests
from lxml import etree

# ===== CONFIGURATION =====
LOCATION = "Arnhem"
RADIUS = "30"
SEARCH_TERMS = [
    "projectleider",
    "werkvoorbereider",
    "monteur",
    "engineer technisch",
    "calculator"
]

OUTPUT_DIR = Path.home() / "recruitin" / "scraper-output"
LOG_DIR = Path("/tmp") / "recruitin_logs"
DB_PATH = OUTPUT_DIR / "vacancies.db"

# Create directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ===== LOGGING SETUP =====
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"indeed_scraper_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== DATA STORAGE =====
VACANCIES: List[Dict] = []
STATS = {
    'total_found': 0,
    'total_unique': 0,
    'errors': 0,
    'by_term': {}
}


# ===== HTML PARSER (to clean HTML from RSS) =====
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text).strip()


def strip_html(html: str) -> str:
    """Remove HTML tags from RSS summary"""
    if not html:
        return ""
    try:
        s = MLStripper()
        s.feed(html)
        return s.get_data()
    except Exception:
        return html


# ===== DATABASE =====
def init_database() -> sqlite3.Connection:
    """Initialize SQLite database voor deduplicatie & history"""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10, check_same_thread=False)
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_hash TEXT UNIQUE NOT NULL,
            functie TEXT NOT NULL,
            bedrijf TEXT,
            plaats TEXT,
            type TEXT,
            salaris TEXT,
            gepost TEXT,
            zoekterm TEXT,
            link TEXT NOT NULL,
            beschrijving TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            seen_before BOOLEAN DEFAULT 0
        )''')

        c.execute('''CREATE INDEX IF NOT EXISTS idx_link_hash ON vacancies(link_hash)''')

        conn.commit()
        logger.info("✅ Database initialized")
        return conn
    except sqlite3.Error as e:
        logger.error(f"❌ Database init error: {str(e)}")
        raise


def check_duplicate(conn: sqlite3.Connection, link: str) -> bool:
    """Check of vacature al bestaat"""
    try:
        link_hash = hashlib.sha256(link.encode()).hexdigest()
        c = conn.cursor()
        c.execute('SELECT id FROM vacancies WHERE link_hash = ? LIMIT 1', (link_hash,))
        return c.fetchone() is not None
    except sqlite3.Error as e:
        logger.warning(f"⚠️  Duplicate check error: {str(e)}")
        return False


def save_to_db(conn: sqlite3.Connection, vacancy: Dict) -> bool:
    """Sla vacature op in database — True=nieuw, False=duplicaat"""
    try:
        link_hash = hashlib.sha256(vacancy['link'].encode()).hexdigest()
        c = conn.cursor()

        c.execute('''INSERT INTO vacancies
            (link_hash, functie, bedrijf, plaats, type, salaris, gepost, zoekterm, link, beschrijving, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (link_hash,
             vacancy.get('functie', 'N/A')[:200],
             vacancy.get('bedrijf', 'N/A')[:200],
             vacancy.get('plaats', 'N/A'),
             vacancy.get('type', 'N/A'),
             vacancy.get('salaris', 'Niet gegeven'),
             vacancy.get('gepost', 'N/A'),
             vacancy.get('zoekterm', 'N/A'),
             vacancy['link'],
             vacancy.get('beschrijving', '')[:500],
             vacancy.get('scraped_at', datetime.now().isoformat())))
        conn.commit()
        return True

    except sqlite3.IntegrityError:
        try:
            link_hash = hashlib.sha256(vacancy['link'].encode()).hexdigest()
            c = conn.cursor()
            c.execute('UPDATE vacancies SET seen_before = 1 WHERE link_hash = ?', (link_hash,))
            conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"⚠️  Could not mark duplicate: {str(e)}")
        return False

    except sqlite3.Error as e:
        logger.error(f"❌ Database save error: {str(e)}")
        return False


# ===== RSS SCRAPING =====
def scrape_indeed_rss(search_term: str, conn: sqlite3.Connection) -> List[Dict]:
    """
    Scrape Indeed vacatures via RSS feed.
    Retourneert lijst van nieuwe vacatures gevonden in deze run.
    """
    logger.info(f"🔍 Fetching RSS: '{search_term}'")
    new_vacancies: List[Dict] = []
    count_new = 0
    count_duplicate = 0

    try:
        # Build RSS URL
        from urllib.parse import quote_plus
        encoded_term = quote_plus(search_term)
        encoded_location = quote_plus(LOCATION)
        url = f"https://nl.indeed.com/rss?q={encoded_term}&l={encoded_location}&radius={RADIUS}&sort=date"

        logger.info(f"   RSS URL: {url}")

        # Fetch with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse with lxml (handles broken XML better)
        try:
            parser = etree.XMLParser(recover=True)  # Recover mode for broken XML
            root = etree.fromstring(response.content, parser=parser)

            # Extract entries manually from XML
            entries = []
            for item in root.findall('.//item'):
                try:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    author_elem = item.find('author')
                    pubdate_elem = item.find('pubDate')

                    entry = {
                        'title': title_elem.text if title_elem is not None else '',
                        'link': link_elem.text if link_elem is not None else '',
                        'description': desc_elem.text if desc_elem is not None else '',
                        'author': author_elem.text if author_elem is not None else '',
                        'pubDate': pubdate_elem.text if pubdate_elem is not None else ''
                    }
                    if entry['title'] and entry['link']:
                        entries.append(entry)
                except Exception as e:
                    logger.debug(f"Error parsing item: {str(e)}")
                    continue

            if not entries:
                logger.warning(f"   ⚠️  No entries found in RSS feed")
                STATS['by_term'][search_term] = {
                    'new': 0,
                    'duplicates': 0,
                    'total': 0,
                    'pages': 1
                }
                return new_vacancies

            logger.info(f"   📰 Found {len(entries)} entries in feed")

        except Exception as e:
            logger.error(f"   ✗ XML parsing error: {str(e)}")
            # Fallback to feedparser
            logger.info(f"   Fallback to feedparser...")
            feed = feedparser.parse(url)
            entries = feed.entries

            if not entries:
                logger.warning(f"   ⚠️  No entries found")
                STATS['by_term'][search_term] = {
                    'new': 0,
                    'duplicates': 0,
                    'total': 0,
                    'pages': 1
                }
                return new_vacancies

        # Process entries
        for idx, entry in enumerate(entries, 1):
            try:
                # Handle both dict and lxml objects
                title = entry.get('title', '') if isinstance(entry, dict) else entry['title']
                link = entry.get('link', '') if isinstance(entry, dict) else entry['link']
                summary = entry.get('description', '') if isinstance(entry, dict) else entry['description']
                author = entry.get('author', '') if isinstance(entry, dict) else entry['author']
                published = entry.get('pubDate', '') if isinstance(entry, dict) else entry['pubDate']

                title = str(title).strip() if title else ''
                link = str(link).strip() if link else ''
                summary = str(summary).strip() if summary else ''
                author = str(author).strip() if author else ''
                published = str(published).strip() if published else ''

                if not title or not link:
                    logger.debug(f"   Skipping entry {idx}: missing title or link")
                    continue

                # Check for duplicate
                if check_duplicate(conn, link):
                    count_duplicate += 1
                    STATS['total_found'] += 1
                    continue

                # Parse description
                description = strip_html(summary)

                # Extract salary if present in summary
                salary = "Niet gegeven"
                if "€" in summary:
                    import re
                    salary_match = re.search(r'€[\d\.,]+ ?- ?€[\d\.,]+|€[\d\.,]+', summary)
                    if salary_match:
                        salary = salary_match.group(0)

                vacancy = {
                    'functie': title[:200],
                    'bedrijf': author if author else 'N/A',
                    'plaats': LOCATION,
                    'type': 'N/A',
                    'salaris': salary,
                    'gepost': published[:20] if published else 'N/A',
                    'zoekterm': search_term,
                    'link': link,
                    'beschrijving': description,
                    'scraped_at': datetime.now().isoformat()
                }

                # Save to database
                if save_to_db(conn, vacancy):
                    VACANCIES.append(vacancy)
                    new_vacancies.append(vacancy)
                    STATS['total_unique'] += 1
                    count_new += 1

                    if count_new % 5 == 0:
                        logger.info(f"   ✓ {count_new} nieuwe vacatures...")
                else:
                    count_duplicate += 1

                STATS['total_found'] += 1

            except Exception as e:
                logger.warning(f"   ⚠️  Error parsing entry {idx}: {str(e)[:100]}")
                STATS['errors'] += 1
                continue

        return new_vacancies

        STATS['by_term'][search_term] = {
            'new': count_new,
            'duplicates': count_duplicate,
            'total': len(entries),
            'pages': 1
        }

        logger.info(
            f"   ✅ '{search_term}': {count_new} NIEUW | "
            f"{count_duplicate} duplicaten | {len(entries)} totaal"
        )

    except requests.RequestException as e:
        logger.error(f"   ✗ Network error fetching RSS for '{search_term}': {str(e)}")
        STATS['errors'] += 1
    except Exception as e:
        logger.error(f"   ✗ Error fetching RSS for '{search_term}': {str(e)}")
        STATS['errors'] += 1

    return new_vacancies


# ===== EXPORT =====
def export_csv(vacancies: List[Dict], ts: str = "") -> Optional[str]:
    """Exporteer alle vacatures naar CSV"""
    if not vacancies:
        logger.warning("Geen vacatures om te exporteren")
        return None
    try:
        csv_file = OUTPUT_DIR / f"indeed_vacatures_{ts or timestamp}.csv"
        fieldnames = ['functie', 'bedrijf', 'plaats', 'type', 'salaris', 'gepost', 'zoekterm', 'link', 'beschrijving']
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(vacancies)
        logger.info(f"✅ CSV geëxporteerd: {csv_file} ({len(vacancies)} rijen)")
        return str(csv_file)
    except IOError as e:
        logger.error(f"❌ CSV export error: {str(e)}")
        return None


def export_json(stats: Dict, ts: str = "") -> Optional[str]:
    """Exporteer statistieken naar JSON (voor Zapier capture)"""
    try:
        json_file = OUTPUT_DIR / f"indeed_stats_{ts or timestamp}.json"
        stats_copy = {
            **stats,
            'timestamp': ts or timestamp,
            'location': LOCATION,
            'radius': RADIUS,
            'search_terms': SEARCH_TERMS,
            'export_time': datetime.now().isoformat(),
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(stats_copy, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Stats geëxporteerd: {json_file}")
        return str(json_file)
    except IOError as e:
        logger.error(f"❌ JSON export error: {str(e)}")
        return None


# ===== MAIN =====
def main():
    """Main execution"""
    logger.info("=" * 70)
    logger.info("Indeed Vacatures Scraper v5.0 - RSS FEED")
    logger.info("=" * 70)
    logger.info(f"Locatie: {LOCATION} ({RADIUS}km radius)")
    logger.info(f"Zoektermen: {', '.join(SEARCH_TERMS)}")
    logger.info(f"Gestart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    conn = None

    try:
        conn = init_database()

        for idx, search_term in enumerate(SEARCH_TERMS, 1):
            try:
                logger.info(f"\n[{idx}/{len(SEARCH_TERMS)}] Verwerken: {search_term}")
                scrape_indeed_rss(search_term, conn)

            except Exception as e:
                logger.error(f"Fout bij scrapen '{search_term}': {str(e)}")
                STATS['errors'] += 1
                continue

        logger.info("\n✅ Alle zoektermen verwerkt")

    except Exception as e:
        logger.error(f"❌ Fatale fout in main: {str(e)}")
        STATS['errors'] += 1

    finally:
        if conn:
            try:
                conn.close()
                logger.info("✅ Database gesloten")
            except Exception as e:
                logger.warning(f"Database close fout: {str(e)}")

    # Finale export
    csv_file = export_csv(VACANCIES)
    json_file = export_json(STATS)

    logger.info("=" * 70)
    logger.info("SCRAPING KLAAR")
    logger.info("=" * 70)
    logger.info(f"Totaal gevonden:   {STATS['total_found']}")
    logger.info(f"Totaal NIEUW:      {STATS['total_unique']}")
    logger.info(f"Totaal fouten:     {STATS['errors']}")
    logger.info("")
    logger.info("Per zoekterm:")
    for term, s in STATS['by_term'].items():
        logger.info(f"  {term}: {s['new']} nieuw | {s['duplicates']} dup | {s.get('total', 0)} totaal")
    logger.info("")
    if csv_file:
        logger.info(f"CSV:  {csv_file}")
    if json_file:
        logger.info(f"JSON: {json_file}")
    logger.info(f"Log:  {log_file}")
    logger.info("=" * 70)

    result = {
        'status': 'success' if STATS['errors'] == 0 else (
            'partial_error' if STATS['total_found'] > 0 else 'error'
        ),
        'csv_file': csv_file,
        'json_file': json_file,
        'log_file': str(log_file),
        'total_found': STATS['total_found'],
        'total_new': STATS['total_unique'],
        'errors': STATS['errors'],
        'timestamp': timestamp
    }
    return result


if __name__ == "__main__":
    try:
        result = main()
        print("\n" + "=" * 70)
        print("JSON OUTPUT VOOR ZAPIER:")
        print("=" * 70)
        print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        logger.info("Scraper gestopt door gebruiker")
    except Exception as e:
        logger.error(f"❌ Fatale fout: {str(e)}")
        print(json.dumps({
            'status': 'error',
            'error': str(e),
            'timestamp': timestamp
        }, indent=2))
