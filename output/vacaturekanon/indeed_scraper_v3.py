#!/usr/bin/env python3
"""
Indeed Vacatures Scraper v3.1 - FIXED
Advanced Playwright-based scraper met error handling, logging, en deduplication
Haalt ALLE vacatures voor technische rollen in Arnhem + 30km
"""

import asyncio
import csv
import json
import sqlite3
import logging
import re
import hashlib
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict, List, Optional

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

OUTPUT_DIR = Path("/mnt/user-data/outputs")
LOG_DIR = Path("/mnt/user-data/outputs/logs")
DB_PATH = Path("/mnt/user-data/outputs/vacancies.db")

# Create directories
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

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

# Thread-safety for global state
vacancy_lock = asyncio.Lock()
stats_lock = asyncio.Lock()

# ===== DATABASE =====
def init_database() -> sqlite3.Connection:
    """Initialize SQLite database for deduplication & history"""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
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
        
        # Create index for faster lookups
        c.execute('''CREATE INDEX IF NOT EXISTS idx_link_hash ON vacancies(link_hash)''')
        
        conn.commit()
        logger.info("✅ Database initialized")
        return conn
    except sqlite3.Error as e:
        logger.error(f"❌ Database init error: {str(e)}")
        raise

def check_duplicate(conn: sqlite3.Connection, link: str) -> bool:
    """Check if vacancy already exists"""
    try:
        link_hash = hashlib.md5(link.encode()).hexdigest()
        c = conn.cursor()
        c.execute('SELECT id FROM vacancies WHERE link_hash = ? LIMIT 1', (link_hash,))
        result = c.fetchone()
        return result is not None
    except sqlite3.Error as e:
        logger.warning(f"⚠️  Duplicate check error: {str(e)}")
        return False

def save_to_db(conn: sqlite3.Connection, vacancy: Dict) -> bool:
    """Save vacancy to database - returns True if new, False if duplicate"""
    try:
        link_hash = hashlib.md5(vacancy['link'].encode()).hexdigest()
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
        # Duplicate exists - mark as seen
        try:
            link_hash = hashlib.md5(vacancy['link'].encode()).hexdigest()
            c = conn.cursor()
            c.execute('UPDATE vacancies SET seen_before = 1 WHERE link_hash = ?', (link_hash,))
            conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"⚠️  Could not mark duplicate: {str(e)}")
        return False
    except sqlite3.Error as e:
        logger.error(f"❌ Database save error: {str(e)}")
        return False

# ===== SCRAPING =====
async def extract_company(link_element) -> str:
    """Extract company name from link element"""
    try:
        # Try to find company in parent structure
        company = await link_element.evaluate(
            """el => {
                const card = el.closest('[class*="job"]');
                if (!card) return null;
                const companyEl = card.querySelector('[class*="company"], [data-company]');
                return companyEl?.textContent?.trim() || null;
            }"""
        )
        return company if company else "N/A"
    except Exception as e:
        logger.debug(f"Company extraction failed: {str(e)}")
        return "N/A"

async def extract_salary(link_element) -> str:
    """Extract salary from job card"""
    try:
        salary = await link_element.evaluate(
            r"""el => {
                const card = el.closest('[class*="job"]');
                if (!card) return null;
                
                // Look for salary elements
                const text = card.textContent || '';
                const regex = /€[\d\.]+/g;
                const matches = text.match(regex);
                
                if (matches && matches.length >= 1) {
                    return matches.slice(0, 2).join(' - ');
                }
                return null;
            }"""
        )
        return salary if salary else "Niet gegeven"
    except Exception as e:
        logger.debug(f"Salary extraction failed: {str(e)}")
        return "Niet gegeven"

async def extract_posting_date(link_element) -> str:
    """Extract posting date from job card"""
    try:
        date = await link_element.evaluate(
            """el => {
                const card = el.closest('[class*="job"]');
                if (!card) return null;
                const dateEl = card.querySelector('[aria-label*="Posted"], [class*="date"]');
                return dateEl?.textContent?.trim() || null;
            }"""
        )
        return date if date else "N/A"
    except Exception as e:
        logger.debug(f"Date extraction failed: {str(e)}")
        return "N/A"

async def wait_for_pagination(page) -> bool:
    """Wait and handle pagination (Load More button)"""
    try:
        # Check for "Load More" button
        load_more_button = await page.query_selector('button[aria-label*="more"]')
        
        if load_more_button:
            # Click load more and wait for new content
            await load_more_button.click()
            await page.wait_for_timeout(2000)
            return True
        
        # Alternative: pagination links
        next_page = await page.query_selector('a[aria-label*="Next"]')
        if next_page:
            await next_page.click()
            await page.wait_for_load_state('domcontentloaded')
            return True
        
        return False
    except Exception as e:
        logger.debug(f"Pagination check: {str(e)}")
        return False

async def scrape_indeed_vacancies(search_term: str, conn: sqlite3.Connection, browser) -> None:
    """
    Scrape Indeed vacancies met robust error handling & pagination
    """
    logger.info(f"🔍 Starting scrape for: {search_term}")
    
    page = None
    try:
        # Create new page in browser context
        page = await browser.new_page()
        
        # Set user agent
        await page.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Build URL with proper encoding
        url = f"https://www.indeed.nl/jobs?q={search_term}&l={LOCATION}&radius={RADIUS}&sort=date"
        logger.info(f"   URL: {url}")
        
        # Navigate with timeout
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)  # Let JS render
        except PlaywrightTimeout as e:
            logger.error(f"   ✗ Timeout loading page: {str(e)}")
            STATS['errors'] += 1
            return
        except Exception as e:
            logger.error(f"   ✗ Navigation error: {str(e)}")
            STATS['errors'] += 1
            return
        
        count_new = 0
        count_duplicate = 0
        pagination_count = 0
        max_pagination = 5  # Max pages to scrape per term
        
        while pagination_count < max_pagination:
            try:
                # Get all job links (data-jk is stable)
                job_links = await page.query_selector_all('a[data-jk]', timeout=5000)
                logger.info(f"   Found {len(job_links)} job links (page {pagination_count + 1})")
                
                if not job_links:
                    logger.info(f"   No more job links found")
                    break
                
                # Process each link
                for idx, link in enumerate(job_links, 1):
                    try:
                        # Get title
                        title = await link.inner_text()
                        if not title or len(title.strip()) == 0:
                            continue
                        
                        # Get URL
                        href = await link.get_attribute('href')
                        if not href:
                            continue
                        
                        full_link = f"https://www.indeed.nl{href}" if href.startswith('/') else href
                        
                        # Check if duplicate BEFORE expensive extractions
                        if check_duplicate(conn, full_link):
                            count_duplicate += 1
                            continue
                        
                        # Extract company, salary, date (with error handling)
                        company = await extract_company(link)
                        salary = await extract_salary(link)
                        posting_date = await extract_posting_date(link)
                        
                        # Create vacancy object
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
                        
                        # Save to database
                        if save_to_db(conn, vacancy):
                            async with vacancy_lock:
                                VACANCIES.append(vacancy)
                            async with stats_lock:
                                STATS['total_unique'] += 1
                            
                            count_new += 1
                            
                            if count_new % 10 == 0:
                                logger.info(f"   ✓ {count_new} new vacancies so far...")
                        else:
                            count_duplicate += 1
                        
                        async with stats_lock:
                            STATS['total_found'] += 1
                        
                    except Exception as e:
                        logger.warning(f"   ⚠️  Error parsing vacancy #{idx}: {str(e)[:100]}")
                        async with stats_lock:
                            STATS['errors'] += 1
                        continue
                
                # Try to load more vacancies
                has_next = await wait_for_pagination(page)
                pagination_count += 1
                
                if not has_next:
                    logger.info(f"   No more pages available")
                    break
                
                await page.wait_for_timeout(2000)  # Rate limiting between pagination
                
            except Exception as e:
                logger.error(f"   ✗ Pagination error: {str(e)}")
                break
        
        # Log stats for this search term
        async with stats_lock:
            STATS['by_term'][search_term] = {
                'new': count_new,
                'duplicates': count_duplicate,
                'total': count_new + count_duplicate,
                'pages': pagination_count
            }
        
        logger.info(f"   ✅ {search_term}: {count_new} NEW | {count_duplicate} duplicates | {pagination_count} pages")
        
    except Exception as e:
        logger.error(f"   ✗ Critical error for {search_term}: {str(e)}")
        async with stats_lock:
            STATS['errors'] += 1
    
    finally:
        if page:
            try:
                await page.close()
            except Exception as e:
                logger.warning(f"Page close error: {str(e)}")

# ===== EXPORT =====
def export_csv(vacancies: List[Dict], ts: str = "") -> Optional[str]:
    """Export to CSV"""
    if not vacancies:
        logger.warning("No vacancies to export")
        return None
    
    try:
        csv_filename = f"indeed_vacatures_{ts or timestamp}.csv"
        csv_file = OUTPUT_DIR / csv_filename
        
        fieldnames = ['functie', 'bedrijf', 'plaats', 'type', 'salaris', 'gepost', 'zoekterm', 'link', 'scraped_at']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(vacancies)
        
        logger.info(f"✅ CSV exported: {csv_file} ({len(vacancies)} rows)")
        return str(csv_file)
    except IOError as e:
        logger.error(f"❌ CSV export error: {str(e)}")
        return None

def export_json(stats: Dict, ts: str = "") -> Optional[str]:
    """Export stats to JSON"""
    try:
        json_filename = f"indeed_stats_{ts or timestamp}.json"
        json_file = OUTPUT_DIR / json_filename
        
        stats_copy = stats.copy()
        stats_copy['timestamp'] = ts or timestamp
        stats_copy['location'] = LOCATION
        stats_copy['radius'] = RADIUS
        stats_copy['search_terms'] = SEARCH_TERMS
        stats_copy['export_time'] = datetime.now().isoformat()
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(stats_copy, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Stats exported: {json_file}")
        return str(json_file)
    except IOError as e:
        logger.error(f"❌ JSON export error: {str(e)}")
        return None

# ===== MAIN =====
async def main():
    """Main execution"""
    logger.info("=" * 70)
    logger.info("Indeed Vacatures Scraper v3.1 - FIXED")
    logger.info("=" * 70)
    logger.info(f"Location: {LOCATION} ({RADIUS}km)")
    logger.info(f"Search terms: {', '.join(SEARCH_TERMS)}")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    conn = None
    playwright = None
    browser = None
    
    try:
        # Initialize database
        conn = init_database()
        
        # Launch Playwright browser ONCE (reuse for all searches)
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage']  # Memory optimization
        )
        logger.info("✅ Browser started")
        
        # Scrape all search terms with single browser instance
        for idx, search_term in enumerate(SEARCH_TERMS, 1):
            try:
                logger.info(f"\n[{idx}/{len(SEARCH_TERMS)}] Processing: {search_term}")
                await scrape_indeed_vacancies(search_term, conn, browser)
                
                # Rate limiting between searches
                if idx < len(SEARCH_TERMS):
                    await asyncio.sleep(3)
                    
            except Exception as e:
                logger.error(f"Failed to scrape {search_term}: {str(e)}")
                async with stats_lock:
                    STATS['errors'] += 1
                continue
        
        logger.info("\n✅ All searches completed")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {str(e)}")
        STATS['errors'] += 1
    
    finally:
        # Cleanup
        if browser:
            try:
                await browser.close()
                logger.info("✅ Browser closed")
            except Exception as e:
                logger.warning(f"Browser close error: {str(e)}")
        
        if playwright:
            try:
                await playwright.stop()
                logger.info("✅ Playwright stopped")
            except Exception as e:
                logger.warning(f"Playwright stop error: {str(e)}")
        
        if conn:
            try:
                conn.close()
                logger.info("✅ Database closed")
            except Exception as e:
                logger.warning(f"Database close error: {str(e)}")
    
    # Export results
    csv_file = export_csv(VACANCIES)
    json_file = export_json(STATS)
    
    # Print summary
    logger.info("=" * 70)
    logger.info("SCRAPING COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total vacancies found: {STATS['total_found']}")
    logger.info(f"Total NEW (unique): {STATS['total_unique']}")
    logger.info(f"Total errors: {STATS['errors']}")
    logger.info("")
    logger.info("By search term:")
    for term, stats in STATS['by_term'].items():
        logger.info(f"  {term}: {stats['new']} NEW | {stats['duplicates']} duplicates | Pages: {stats.get('pages', 1)}")
    logger.info("")
    if csv_file:
        logger.info(f"CSV: {csv_file}")
    if json_file:
        logger.info(f"JSON: {json_file}")
    logger.info(f"Log: {log_file}")
    logger.info("=" * 70)
    
    # Return for Zapier/external calling
    return {
        'status': 'success' if STATS['errors'] < STATS['total_found'] else 'partial_error',
        'csv_file': csv_file,
        'json_file': json_file,
        'log_file': str(log_file),
        'total_found': STATS['total_found'],
        'total_new': STATS['total_unique'],
        'errors': STATS['errors'],
        'timestamp': timestamp
    }

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        # Print JSON for Zapier capture
        print("\n" + "=" * 70)
        print("JSON OUTPUT FOR ZAPIER:")
        print("=" * 70)
        print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        print(json.dumps({
            'status': 'error',
            'error': str(e),
            'timestamp': timestamp
        }, indent=2))
