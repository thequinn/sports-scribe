import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

"""
Goal:
- Retrieve the Premier League fixtures page from FBRef.com.
    https://fbref.com/en/comps/9/2024-2025/schedule/2024-2025-Premier-League-Scores-and-Fixtures

Issue:
- HTTP 403 Forbidden Error:
  - The website was blocking requests due to Cloudflare bot detection

Solutions Implemented:
  1. Enhanced HTTP Headers:
  - Added comprehensive browser-like headers to mimic real user

  2. Session Management:
  - Used requests.Session() for better cookie and connection handling

  3. Retry Logic:
  - Implemented intelligent retry mechanism with random delays

  4. Selenium Fallback:
  - Added Selenium WebDriver as a fallback when requests fail

  5. Cloudflare Bypass:
  - Selenium successfully handles JavaScript-based bot detection

Key Features:
•  Dual Strategy: First tries lightweight requests, then falls back to Selenium
•  Bot Detection Evasion: Multiple techniques to appear as a real browser
•  Error Handling: Comprehensive error reporting and troubleshooting suggestions
•  File Output: Successfully saved HTML content to fbref_premier_league_2024_25.html

Why use Selenium?
- BeautifulSoup is great for static HTML, but if the page loads content dynamically, we need Selenium. Unfortunately many modern websites dynamically load content using JavaScript, meaning some elements (like tables, buttons, or text) are not present in the initial HTML source when you request the page using requests or BeautifulSoup. Instead, the page executes JavaScript to fetch and display the content after the page has initially loaded. Luckily Selenium can solve this problem.

Result:
- The Selenium method bypassed Cloudflare's protection, and the data is ready for parsing and extraction.
"""

"""
Data Requirements:

essential fields: (Must have)
  - match_id, date, league, season
  - home_team, away_team
  - home_score, away_score
  - source

additional fields: (Optional)
  - referee, attendance, venue
  - half_time_scores
  - basic_statistics (shots, possession)
"""


def download_single_html_page(url):
    """
    Fetches a HTML page from the specified URL and saves it locally.

    Example link to download html data for premier league 2024-25
    https://fbref.com/en/comps/9/2024-2025/schedule/2024-2025-Premier-League-Scores-and-Fixtures
    """

    base_url = "https://fbref.com/en/comps/9/2024-2025/schedule/2024-2025-Premier-League-Scores-and-Fixtures"

    # Create a session to maintain cookies and connection pooling
    session = requests.Session()

    # Added comprehensive browser-like headers to mimic real user requestsand avoid 403 errors
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": "1",
        "Referer": "https://fbref.com/",
    }
    session.headers.update(headers)

    # Introduce random delay to mimic human behavior
    delay = random.uniform(1.0, 3.0)
    print(f"Sleeping for {delay:.2f} seconds to mimic human behavior.")
    time.sleep(delay)

    print(f"Downloading HTML page from {url}...")

    # First, visit the main page to establish session
    try:
        print("Establishing session by visiting main page...")
        main_response = session.get("https://fbref.com/", timeout=30)
        print(f"Main page status: {main_response.status_code}")
        time.sleep(random.uniform(1, 3))
    except Exception as e:
        print(f"Warning: Could not establish session: {e}")

    try:
        # Retry logic for handling transient issues
        for i in range(3):
            print(f"Attempt {i+1} of 3...")
            response = session.get(url, timeout=30)

            if response.status_code == 200:
                html_content = response.text
                print(
                    f"Request success. HTML content length: {len(html_content)} characters"
                )
                return html_content
            elif response.status_code == 403:
                print(
                    f"403 Forbidden error. This might be due to rate limiting or bot detection."
                )
                if i < 2:  # Don't sleep on last attempt
                    delay = random.uniform(5, 15)
                    print(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)
            else:
                print(f"Unexpected status code: {response.status_code}")
                if i < 2:
                    time.sleep(random.uniform(2, 8))

        # If we get here, all retries failed
        response.raise_for_status()  # This will raise the last error

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from {url}. Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Response headers: {dict(e.response.headers)}")
            if e.response.text:
                print(f"Response preview: {e.response.text[:500]}...")

        # Suggest alternative approaches
        print("\nSuggested alternatives:")
        print("1. Use selenium with a real browser")
        print("2. Check if FBRef has an official API")
        print("3. Try accessing the data during off-peak hours")
        print("4. Consider using a proxy or VPN")

        raise ValueError(f"Failed to fetch data from {url}: {e}")

    finally:
        session.close()


def download_with_selenium(url):
    """
    Uses Selenium WebDriver to handle JavaScript-based bot detection (like Cloudflare).
    """
    driver = None
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Uncomment the next line to run in headless mode
        # chrome_options.add_argument('--headless')

        # User agent to mimic real browser
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        print("Starting Chrome WebDriver...")
        # Set Chrome binary location for macOS
        chrome_options.binary_location = (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        driver = webdriver.Chrome(options=chrome_options)

        # Remove the webdriver property to avoid detection
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print(f"Navigating to {url} ...")
        driver.get(url)

        # Waiting for the webpage to finish loading and for any anti-bot “challenge” screens (like “Just a moment…” or “Checking your browser…”) from Cloudflare to go away before continuing.
        print("Waiting for page to load and any challenges to complete...")
        try:
            # Wait for either the main content to load or timeout
            WebDriverWait(driver, 30).until(
                lambda d: "Just a moment" not in d.title
                and "Checking your browser" not in d.page_source
            )
            print("Challenge completed or page loaded successfully.")
        except TimeoutException:
            print("Timeout waiting for challenge completion, but proceeding anyway...")

        # Additional wait to ensure page is fully loaded
        time.sleep(random.uniform(2, 5))

        # Get the page source
        html_content = driver.page_source

        # Check if we got the actual content
        if "Just a moment" in html_content or "Checking your browser" in html_content:
            raise ValueError("Still showing Cloudflare challenge page")

        print(
            f"Successfully retrieved page. Content length: {len(html_content)} characters"
        )

        return html_content

    except WebDriverException as e:
        error_msg = f"WebDriver error: {e}"
        print(error_msg)

        # Check if Chrome is installed
        print("\nTroubleshooting:")
        print("1. Make sure Chrome browser is installed")
        print("2. Install ChromeDriver: brew install --cask chromedriver")
        print("3. Or use: pip install webdriver-manager")

        raise ValueError(error_msg)

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise ValueError(f"Failed to scrape with Selenium: {e}")

    finally:
        if driver:
            print("Closing browser...")
            driver.quit()


def save_html_to_file(html_content, filename):
    """Save HTML content to a file."""

    cur_dir = os.path.dirname((os.path.abspath(__file__)))

    data_raw_folder = os.path.join(cur_dir, "..", "data", "raw")
    data_raw_folder = os.path.normpath(data_raw_folder)

    filepath = os.path.join(data_raw_folder, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML content saved to {filepath}")


def generate_request_url(league_id, league_name, season):
    """
    Generate url based on league and season.
        ex. Premier League 2024-2025
            "https://fbref.com/en/comps/9/2024-2025/schedule/2024-2025-Premier-League-Scores-and-Fixtures"

        ex. Champions League 2023-2024
            "https://fbref.com/en/comps/8/2024-2025/schedule/2024-2025-Champions-League-Scores-and-Fixtures"

        ex. La Liga 2023-2024
            "https://fbref.com/en/comps/12/2023-2024/schedule/2023-2024-La-Liga-Scores-and-Fixtures"
    """
    # league_id = 9  # Premier League
    season_code = f"{str(season)}-{str(season+1)}"
    # league_name = "Premier-League"  # Premier League
    endpoint = f"{season_code}-{league_name}-Scores-and-Fixtures"

    url = f"https://fbref.com/en/comps/{league_id}/{season_code}/schedule/{endpoint}"

    return url


if __name__ == "__main__":

    """
    league_ids = [9, 8, 12]  # Premier League, Champions League, La Liga
    league_names = ["Premier-League", "Champions-League", "La-Liga"]
    seasons= [2020, 2021, 2022, 2023, 2024]
    """
    league_ids = [8]  # Premier League, Champions League, La Liga
    league_names = ["Champions-League"]
    seasons = [2024]

    # url = "https://fbref.com/en/comps/9/2024-2025/schedule/2024-2025-Premier-League-Scores-and-Fixtures"

    # print("Attempting to scrape with requests...")
    # try:
    #     html_content = download_single_html_page(urls[0])
    #     print("\nSuccess with requests method!")

    # except ValueError as e:
    #     print(f"\nRequests method failed: {e}")
    #     print("\nFalling back to Selenium method...")
    #     try:

    #         for season in seasons:
    #             for league_id, league_name in zip(league_ids, league_names):
    #                 url = generate_request_url(league_id, league_name, season)
    #                 print(f"\nGenerated URL: {url}")

    #                 html_content = download_with_selenium(url)
    #             print("Success with Selenium method!")

    #             # Save the HTML content to a file for inspection
    #             output_file = f"fbref_{league_name}_{season}_{season+1}.html"
    #         save_html_to_file(html_content, output_file)

    #     except ValueError as selenium_error:
    #         print(f"\nSelenium method also failed: {selenium_error}")
    #         print("\nBoth methods failed. This site has strong bot protection.")

    print(
        "\nfbfre.com has strong bot protection, requests method is not reliable. Using Selenium method only..."
    )
    try:

        for season in seasons:
            for league_id, league_name in zip(league_ids, league_names):
                url = generate_request_url(league_id, league_name, season)
                print(f"\nGenerated URL: {url}")

                html_content = download_with_selenium(url)
            print("Success with Selenium method!")

            # Save the HTML content to a file for inspection
            output_file = f"fbref_{league_name}_{season}_{season+1}.html"
        save_html_to_file(html_content, output_file)

    except ValueError as selenium_error:
        print(f"\nSelenium method also failed: {selenium_error}")
        print("\nBoth methods failed. This site has strong bot protection.")
