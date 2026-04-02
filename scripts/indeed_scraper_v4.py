#!/opt/homebrew/bin/python3
"""
Indeed Vacatures Scraper v4.0 - FIXED + ANTI-BOT
Advanced Playwright-based scraper met:
  - playwright-stealth integratie
  - realistisch browser fingerprint
  - menselijke delay simulatie
  - URL encoding fix
  - correcte Playwright API calls
  - SHA256 deduplication
  - tussentijdse CSV export
  - SQLite check_same_thread fix
"""

import asyncio
import csv
import json
import sqlite3
import logging
import hashlib
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict, List, Optional

# playwright-stealth v2.x gebruikt Stealth class als context manager
try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

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

OUTPUT_DIR = Path.home() / "Desktop" / "recruitin_scraper_output"
LOG_DIR = Path("/tmp") / "recruitin_logs"
DB_PATH = Path.home() / "Desktop" / "recruitin_scraper_output" / "vacancies.db"

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

vacancy_lock = asyncio.Lock()
stats_lock = asyncio.Lock()

# ===== USER AGENTS POOL =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1920, "height": 1080},
    {"width": 1280, "height": 800},
]

# ===== DATABASE =====
def init_database() -> sqlite3.Connection:
    """Initialize SQLite database voor deduplicatie & history"""
    try:
        # check_same_thread=False voor async compatibiliteit
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
            (link_hash, functie, bedrijf, plaats, type, salaris, gepost, zoekterm, link, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (link_hash,
             vacancy.get('functie', 'N/A')[:200],
             vacancy.get('bedrijf', 'N/A')[:200],
             vacancy.get('plaats', 'N/A'),
             vacancy.get('type', 'N/A'),
             vacancy.get('salaris', 'Niet gegeven'),
             vacancy.get('gepost', 'N/A'),
             vacancy.get('zoekterm', 'N/A'),
             vacancy['link'],
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


# ===== ANTI-BOT: HUMAN BEHAVIOR SIMULATION =====
async def human_delay(min_ms: int = 600, max_ms: int = 2800) -> None:
    """Simuleer menselijke pauze met willekeurige variatie"""
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    await asyncio.sleep(delay)


async def human_scroll(page) -> None:
    """Scroll langzaam omlaag zoals een mens"""
    scroll_steps = random.randint(3, 7)
    for _ in range(scroll_steps):
        scroll_y = random.randint(200, 500)
        await page.evaluate(
            f"window.scrollBy({{top: {scroll_y}, left: 0, behavior: 'smooth'}})"
        )
        await human_delay(300, 900)


async def human_mouse_move(page) -> None:
    """Beweeg muis willekeurig over het scherm"""
    try:
        moves = random.randint(2, 4)
        for _ in range(moves):
            x = random.randint(100, 1200)
            y = random.randint(100, 600)
            await page.mouse.move(x, y, steps=random.randint(8, 20))
            await human_delay(80, 300)
    except Exception:
        pass  # Muis beweging is optioneel, nooit fatal


async def create_stealth_context(playwright):
    """
    Maak een volledig gecamoufleerd browser context aan.
    Meest effectieve anti-bot laag.
    """
    user_agent = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)

    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-infobars',
            '--window-size=1920,1080',
            f'--user-agent={user_agent}',
        ]
    )

    context = await browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        locale="nl-NL",
        timezone_id="Europe/Amsterdam",
        # Arnhem coördinaten — meer authentiek voor Indeed.nl
        geolocation={"latitude": 51.9851, "longitude": 5.8987},
        permissions=["geolocation"],
        extra_http_headers={
            "Accept-Language": "nl-NL,nl;q=0.9,en-GB;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
        }
    )

    logger.info(f"✅ Browser context aangemaakt | UA: {user_agent[:50]}...")
    return browser, context


# ===== SCRAPING HELPERS =====
async def extract_company(link_element) -> str:
    """Extract bedrijfsnaam uit job card"""
    try:
        company = await link_element.evaluate(
            """el => {
                const card = el.closest('[class*="job"]');
                if (!card) return null;
                const el2 = card.querySelector('[class*="company"], [data-company], [class*="employer"]');
                return el2?.textContent?.trim() || null;
            }"""
        )
        return company if company else "N/A"
    except Exception:
        return "N/A"


async def extract_salary(link_element) -> str:
    """Extract salaris uit job card"""
    try:
        salary = await link_element.evaluate(
            r"""el => {
                const card = el.closest('[class*="job"]');
                if (!card) return null;
                const text = card.textContent || '';
                const matches = text.match(/€[\d\.,]+/g);
                if (matches && matches.length >= 1) {
                    return matches.slice(0, 2).join(' - ');
                }
                return null;
            }"""
        )
        return salary if salary else "Niet gegeven"
    except Exception:
        return "Niet gegeven"


async def extract_posting_date(link_element) -> str:
    """Extract plaatsingsdatum uit job card"""
    try:
        date = await link_element.evaluate(
            """el => {
                const card = el.closest('[class*="job"]');
                if (!card) return null;
                const dateEl = card.querySelector('[aria-label*="Posted"], [class*="date"], [class*="Date"]');
                return dateEl?.textContent?.trim() || null;
            }"""
        )
        return date if date else "N/A"
    except Exception:
        return "N/A"


async def dismiss_cookie_consent(page) -> bool:
    """
    Sluit de cookie consent banner op Indeed.nl.
    Dit is de #1 oorzaak van 0 resultaten op Nederlandse sites.
    """
    consent_selectors = [
        'button[id*="onetrust-accept"]',
        'button[aria-label*="Accept"]',
        'button[aria-label*="Accepteer"]',
        'button[aria-label*="akkoord"]',
        '#onetrust-accept-btn-handler',
        'button:has-text("Akkoord")',
        'button:has-text("Accept all")',
        'button:has-text("Alle cookies accepteren")',
        '[data-testid="cookie-consent-accept"]',
    ]
    for selector in consent_selectors:
        try:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                await human_delay(800, 1500)
                logger.info(f"   🍪 Cookie consent gesloten via: {selector}")
                return True
        except Exception:
            continue
    return False


async def diagnose_page(page, search_term: str) -> None:
    """
    Log paginatitel en maak screenshot als er geen vacatures gevonden worden.
    Helpt debuggen: CAPTCHA? Consent banner? Lege pagina?
    """
    try:
        title = await page.title()
        url = page.url
        logger.warning(f"   🔎 Diagnose — Titel: '{title}' | URL: {url[:80]}")

        # Screenshot voor visuele inspectie
        screenshot_path = OUTPUT_DIR / f"debug_{search_term.replace(' ', '_')}_{timestamp}.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        logger.warning(f"   📸 Screenshot opgeslagen: {screenshot_path.name}")

        # Check voor CAPTCHA indicators
        page_text = await page.evaluate("document.body?.innerText?.substring(0, 500) || ''")
        if any(word in page_text.lower() for word in ['captcha', 'robot', 'verify', 'beveilig']):
            logger.error("   🚨 CAPTCHA of bot-detectie gedetecteerd!")
        elif any(word in page_text.lower() for word in ['cookie', 'consent', 'akkoord', 'privacy']):
            logger.warning("   🍪 Consent/cookie pagina gedetecteerd — consent handler mislukt")
        else:
            logger.info(f"   Paginatekst preview: {page_text[:200]}")
    except Exception as e:
        logger.debug(f"Diagnose fout: {str(e)}")



async def wait_for_next_page(page) -> bool:
    """Detecteer en klik op volgende pagina"""
    try:
        load_more = await page.query_selector('button[aria-label*="more"], button[aria-label*="meer"]')
        if load_more:
            await human_mouse_move(page)
            await load_more.click()
            await page.wait_for_timeout(2500)
            return True

        next_page = await page.query_selector('a[aria-label*="Next"], a[aria-label*="Volgende"]')
        if next_page:
            await human_mouse_move(page)
            await next_page.click()
            await page.wait_for_load_state('domcontentloaded')
            await human_delay(1500, 3000)
            return True

        return False
    except Exception as e:
        logger.debug(f"Pagination check: {str(e)}")
        return False


def flush_csv_intermediate(vacancies: List[Dict], search_term: str) -> None:
    """Tussentijdse CSV export per zoekterm (failsafe)"""
    if not vacancies:
        return
    try:
        safe_term = search_term.replace(" ", "_")
        csv_file = OUTPUT_DIR / f"temp_{safe_term}_{timestamp}.csv"
        fieldnames = ['functie', 'bedrijf', 'plaats', 'type', 'salaris', 'gepost', 'zoekterm', 'link', 'scraped_at']
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(vacancies)
        logger.info(f"   💾 Tussentijdse export: {csv_file.name} ({len(vacancies)} rijen)")
    except IOError as e:
        logger.warning(f"   ⚠️  Tussentijdse export mislukt: {str(e)}")


# ===== MAIN SCRAPE FUNCTION =====
async def scrape_indeed_vacancies(
    search_term: str,
    conn: sqlite3.Connection,
    context,
) -> List[Dict]:
    """
    Scrape Indeed vacatures voor één zoekterm.
    Retourneert lijst van nieuwe vacatures gevonden in deze run.
    """
    logger.info(f"🔍 Start scrape: '{search_term}'")
    new_vacancies_this_term: List[Dict] = []
    page = None

    try:
        page = await context.new_page()

        # Stealth toepassen via apply_stealth_async (v2.x API)
        if STEALTH_AVAILABLE:
            stealth_instance = Stealth()
            await stealth_instance.apply_stealth_async(page)
            logger.info("   🥷 Stealth mode actief (v2.x)")
        else:
            logger.warning("   ⚠️  playwright-stealth niet beschikbaar")

        # Verberg automation via JS override (extra laag bovenop stealth)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['nl-NL', 'nl', 'en-GB'] });
            window.chrome = { runtime: {} };
        """)

        # URL correct encoderen — FIX voor spaties in zoektermen
        encoded_term = quote_plus(search_term)
        encoded_location = quote_plus(LOCATION)
        url = f"https://www.indeed.nl/jobs?q={encoded_term}&l={encoded_location}&radius={RADIUS}&sort=date"
        logger.info(f"   URL: {url}")

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await human_delay(1500, 3000)

            # Stap 1: Cookie consent sluiten (moet VOOR scraping)
            consented = await dismiss_cookie_consent(page)
            if consented:
                await human_delay(1000, 2000)  # Wacht op herlaad na consent

            await human_scroll(page)  # Scroll omlaag voor realistisch gedrag
        except PlaywrightTimeout:
            logger.error(f"   ✗ Timeout laden pagina voor: {search_term}")
            async with stats_lock:
                STATS['errors'] += 1
            return new_vacancies_this_term
        except Exception as e:
            logger.error(f"   ✗ Navigatie error: {str(e)}")
            async with stats_lock:
                STATS['errors'] += 1
            return new_vacancies_this_term

        count_new = 0
        count_duplicate = 0
        pagination_count = 0
        max_pagination = 5

        while pagination_count < max_pagination:
            try:
                # Wacht op job links — probeer data-jk (stabiel) én fallback selectors
                job_links = []
                for selector in ['a[data-jk]', 'a[id^="job_"]', '.jobCard_mainContent a', 'h2.jobTitle a']:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        job_links = await page.query_selector_all(selector)
                        if job_links:
                            logger.info(f"   Selector gebruikt: {selector}")
                            break
                    except PlaywrightTimeout:
                        continue

                if not job_links:
                    logger.warning(f"   ⚠️  Geen vacatures op pagina {pagination_count + 1} — diagnose:")
                    await diagnose_page(page, search_term)
                    break

                for idx, link in enumerate(job_links, 1):
                    try:
                        title = await link.inner_text()
                        if not title or not title.strip():
                            continue

                        href = await link.get_attribute('href')
                        if not href:
                            continue

                        full_link = f"https://www.indeed.nl{href}" if href.startswith('/') else href

                        # Deduplicatie check VóórDat we dure extractions doen
                        if check_duplicate(conn, full_link):
                            count_duplicate += 1
                            async with stats_lock:
                                STATS['total_found'] += 1
                            continue

                        company = await extract_company(link)
                        salary = await extract_salary(link)
                        posting_date = await extract_posting_date(link)

                        vacancy = {
                            'functie': title.strip()[:200],
                            'bedrijf': company,
                            'plaats': LOCATION,
                            'type': 'N/A',
                            'salaris': salary,
                            'gepost': posting_date,
                            'zoekterm': search_term,
                            'link': full_link,
                            'scraped_at': datetime.now().isoformat()
                        }

                        if save_to_db(conn, vacancy):
                            async with vacancy_lock:
                                VACANCIES.append(vacancy)
                                new_vacancies_this_term.append(vacancy)
                            async with stats_lock:
                                STATS['total_unique'] += 1
                            count_new += 1

                            if count_new % 10 == 0:
                                logger.info(f"   ✓ {count_new} nieuwe vacatures...")
                        else:
                            count_duplicate += 1

                        async with stats_lock:
                            STATS['total_found'] += 1

                        # Kleine random delay tussen vacatures (mens-gedrag)
                        if idx % 5 == 0:
                            await human_delay(300, 800)

                    except Exception as e:
                        logger.warning(f"   ⚠️  Fout bij vacature #{idx}: {str(e)[:100]}")
                        async with stats_lock:
                            STATS['errors'] += 1
                        continue

                # Volgende pagina
                has_next = await wait_for_next_page(page)
                pagination_count += 1

                if not has_next:
                    logger.info(f"   Geen volgende pagina meer")
                    break

                await human_delay(2000, 4000)  # Rate limiting tussen pagina's

            except Exception as e:
                logger.error(f"   ✗ Paginering error: {str(e)}")
                break

        # Tussentijdse export als failsafe
        flush_csv_intermediate(new_vacancies_this_term, search_term)

        async with stats_lock:
            STATS['by_term'][search_term] = {
                'new': count_new,
                'duplicates': count_duplicate,
                'total': count_new + count_duplicate,
                'pages': pagination_count
            }

        logger.info(
            f"   ✅ '{search_term}': {count_new} NIEUW | "
            f"{count_duplicate} duplicaten | {pagination_count} pagina's"
        )

    except Exception as e:
        logger.error(f"   ✗ Kritieke fout voor '{search_term}': {str(e)}")
        async with stats_lock:
            STATS['errors'] += 1

    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass

    return new_vacancies_this_term


# ===== EXPORT =====
def export_csv(vacancies: List[Dict], ts: str = "") -> Optional[str]:
    """Exporteer alle vacatures naar CSV"""
    if not vacancies:
        logger.warning("Geen vacatures om te exporteren")
        return None
    try:
        csv_file = OUTPUT_DIR / f"indeed_vacatures_{ts or timestamp}.csv"
        fieldnames = ['functie', 'bedrijf', 'plaats', 'type', 'salaris', 'gepost', 'zoekterm', 'link', 'scraped_at']
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
async def main():
    """Main execution"""
    logger.info("=" * 70)
    logger.info("Indeed Vacatures Scraper v4.0 - FIXED + ANTI-BOT")
    logger.info("=" * 70)
    logger.info(f"Locatie: {LOCATION} ({RADIUS}km radius)")
    logger.info(f"Zoektermen: {', '.join(SEARCH_TERMS)}")
    logger.info(f"Stealth mode: {'✅ playwright-stealth geladen' if STEALTH_AVAILABLE else '⚠️  niet beschikbaar'}")
    logger.info(f"Gestart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    conn = None
    playwright = None
    browser = None
    context = None

    try:
        conn = init_database()

        playwright = await async_playwright().start()
        browser, context = await create_stealth_context(playwright)
        logger.info("✅ Browser gestart (stealth context)")

        for idx, search_term in enumerate(SEARCH_TERMS, 1):
            try:
                logger.info(f"\n[{idx}/{len(SEARCH_TERMS)}] Verwerken: {search_term}")
                await scrape_indeed_vacancies(search_term, conn, context)

                if idx < len(SEARCH_TERMS):
                    # Menselijke pauze tussen zoektermen
                    wait_sec = random.uniform(4, 8)
                    logger.info(f"   ⏳ Wachten {wait_sec:.1f}s voor volgende zoekterm...")
                    await asyncio.sleep(wait_sec)

            except Exception as e:
                logger.error(f"Fout bij scrapen '{search_term}': {str(e)}")
                async with stats_lock:
                    STATS['errors'] += 1
                continue

        logger.info("\n✅ Alle zoektermen verwerkt")

    except Exception as e:
        logger.error(f"❌ Fatale fout in main: {str(e)}")
        async with stats_lock:
            STATS['errors'] += 1

    finally:
        # Nette cleanup
        if context:
            try:
                await context.close()
                logger.info("✅ Context gesloten")
            except Exception as e:
                logger.warning(f"Context close fout: {str(e)}")
        if browser:
            try:
                await browser.close()
                logger.info("✅ Browser gesloten")
            except Exception as e:
                logger.warning(f"Browser close fout: {str(e)}")
        if playwright:
            try:
                await playwright.stop()
                logger.info("✅ Playwright gesloten")
            except Exception as e:
                logger.warning(f"Playwright stop fout: {str(e)}")
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
        logger.info(f"  {term}: {s['new']} nieuw | {s['duplicates']} dup | {s.get('pages', 1)} pagina's")
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
        result = asyncio.run(main())
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
