from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
import sys

def scrape_webpage(url: str) -> str:
    """
    Scrapes all visible text from ANY public URL using Playwright.
    Optimized for general website audits (waiting for load, stripping scripts).
    """
    if not url:
        return "No URL provided."

    print(f"      [Scraper] Starting scrape for: {url}")
    sys.stdout.flush()

    try:
        with sync_playwright() as p:
            # Launch browser (headless)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"      [Scraper] Navigating...")
            sys.stdout.flush()
            
            # 'domcontentloaded' is faster than 'networkidle' and usually sufficient for text
            # Timeout set to 30s to fail fast if site is down
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            print(f"      [Scraper] Page loaded. Extracting content...")
            sys.stdout.flush()

            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")

        # Remove script, style, and navigation elements to get clean "body" text
        for script in soup(["script", "style", "noscript", "header", "footer", "nav", "svg"]):
            script.extract()

        # Find the main body
        body = soup.find("body")

        if body:
            # Get text, strip extra whitespace
            text = body.get_text(" ", strip=True)
            # Clean up multiple spaces to single spaces
            clean_text = " ".join(text.split())
            
            # --- UNLIMITED SCRAPE FOR FULL DEBUG VISIBILITY ---
            # (No truncation logic here)
            
            print(f"      [Scraper] Successfully extracted {len(clean_text)} characters.")
            return clean_text
        else:
            return "Scrape failed: Could not find <body> tag."

    except TimeoutError:
        print(f"      [Scraper Error] Timeout exceeded for {url}.")
        return "Scrape failed: Page timed out."
    except Exception as e:
        print(f"      [Scraper Error] {e} for {url}")
        return f"Scrape failed: {e}"

if __name__ == "__main__":
    # Quick test
    print(scrape_webpage("https://www.casesbysource.com/"))