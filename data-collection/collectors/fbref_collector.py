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


def extract_elements(soup, element):
    """Scrape data from HTML content."""

    """Extract Dates first for a try..."""
    # Todo: extract essential fields

    # For example, to extract dates:
    # - Find all the <td> elements that have the attribute data-stat="date"
    #
    # FBref.com uses these data-stat attributes to label every single piece of data in their tables.
    data_cells = soup.find_all("td", attrs={"data-stat": element})

    # Create an empty list to hold our clean dates
    all_data = []

    # Loop through every cell we found
    for cell in data_cells:
        data_text = cell.get_text()  # Get the visible text (e.g., "2024-08-17")
        if data_text:  # Make sure it's not an empty string
            all_data.append(data_text)

    # print(all_dates)
    return all_data


def create_csv(extracted_data, filepath):
    """Create a CSV file from the extracted data (Essential fields for DB)"""
    pd.DataFrame(extracted_data).to_csv(filepath, index=False)
    print(f"CSV file created: {filepath}")


def convert_score_to_home_score_and_away_score(extracted_data):
    """
    score has various formats:
    •  Regular scores: "0–3", "3–1", "2–0"
    •  Penalty scores: "(1) 0–1 (4)", "(5) 1–2 (6)", "(2) 1–0 (4)"
    """

    # Clear existing home_score and away_score data since fill_columns already populated them
    extracted_data["home_score"] = []
    extracted_data["away_score"] = []

    for idx, score in enumerate(extracted_data["score"]):
        try:
            # Handle penalty scores like "(1) 0–1 (4)" or "(5) 1–2 (6)"
            if score.startswith("(") and ")" in score:
                # Extract the main score part (e.g., "0–1" from "(1) 0–1 (4)")
                # Find the pattern: ") SCORE ("
                start_idx = score.find(") ") + 2
                end_idx = score.find(" (", start_idx)

                # Handle cases where there might not be trailing penalty info
                if end_idx == -1:
                    main_score = score[start_idx:]
                else:
                    main_score = score[start_idx:end_idx]
            else:
                main_score = score

            # Split on the en dash (–) character, not regular hyphen (-)
            if "–" in main_score:
                home_score, away_score = main_score.split("–")
            elif "-" in main_score:
                # Fallback to regular hyphen if en dash not found
                home_score, away_score = main_score.split("-")
            else:
                print(f"Warning: Could not parse score at index {idx}: '{score}'")
                home_score, away_score = "", ""

            # Clean up any whitespace
            home_score = home_score.strip()
            away_score = away_score.strip()

            extracted_data["home_score"].append(home_score)
            extracted_data["away_score"].append(away_score)

        except Exception as e:
            print(f"Error parsing score at index {idx}: '{score}' - {e}")
            # Add empty scores for failed parsing
            extracted_data["home_score"].append("")
            extracted_data["away_score"].append("")


def fill_columns(extracted_data):
    # Initialize missing keys as empty lists
    required_keys = [
        "match_id",
        "league",
        "season",
        "home_score",
        "away_score",
        "source",
    ]
    for key in required_keys:
        if key not in extracted_data:
            extracted_data[key] = []

    # Insert other fields needed
    for i in range(len(extracted_data["date"])):
        extracted_data["match_id"].append(i + 1)
        extracted_data["league"].append("Champions League")
        extracted_data["season"].append("2024-2025")
        extracted_data["home_score"].append("")
        extracted_data["away_score"].append("")
        extracted_data["source"].append("fbref.com")

    return extracted_data


if __name__ == "__main__":

    """
    league_ids = [9, 8, 12]  # Premier League, Champions League, La Liga
    league_names = ["Premier-League", "Champions-League", "La-Liga"]
    seasons= [2020, 2021, 2022, 2023, 2024]
    """
    """
    league_ids = [8]  # Premier League, Champions League, La Liga
    league_names = ["Champions-League"]
    seasons = [2024]
    """
    """
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
    """
