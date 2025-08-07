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


def extract_columns(soup, data_fields, html_filepath):
    # A quick check to make sure the file exists before we try to read it
    if not os.path.exists(html_filepath):
        print(f"Error: File not found at {html_filepath}")
        print("Please update the 'html_filepath' variable with the correct location.")
    else:
        parsed_rows = []
        # Find the specific table we care about using BeautifulSoup
        table = soup.find("table", class_="stats_table")

        if table:
            for row in table.find("tbody").find_all("tr"):

                # For each row, find the specific cells '<td>' by their 'data-stat' attribute
                date_cell = row.find("td", {"data-stat": "date"})
                score_cell = row.find("td", {"data-stat": "score"})
                home_team_cell = row.find("td", {"data-stat": "home_team"})
                away_team_cell = row.find("td", {"data-stat": "away_team"})

                # Extract the text from each cell, checking if the cell was found
                date = date_cell.text.strip() if date_cell else ""
                score = score_cell.text.strip() if score_cell else ""
                home_team = home_team_cell.text.strip() if home_team_cell else ""
                away_team = away_team_cell.text.strip() if away_team_cell else ""

                # Create a dictionary for each row
                parsed_rows.append(
                    {
                        "date": date,
                        "score": score,
                        "home_team": home_team,
                        "away_team": away_team,
                    }
                )

        # Convert our list of dictionaries into a pandas DataFrame
        if parsed_rows:
            # 2nd arg preserves the order of the columns
            df_bs = pd.DataFrame(
                parsed_rows, columns=["date", "score", "home_team", "away_team"]
            )
            print("\nSuccess! Extracted columns using BeautifulSoup:\n")
            print(df_bs.head())
        else:
            print("\nFailed to extract columns using BeautifulSoup.")
    return df_bs


def convert_score_to_home_score_and_away_score(score_column):
    """
    score has various formats:
    •  Regular scores: "0–3", "3–1", "2–0"
    •  Penalty scores: "(1) 0–1 (4)", "(5) 1–2 (6)", "(2) 1–0 (4)"
    """
    home_scores = []
    away_scores = []
    for score in score_column:
        if score.startswith("(") and ")" in score:
            # Extract the main score part (e.g., "0–1" from "(1) 0–1 (4)")
            main_score = score[score.find(")") + 1 : score.find(" (")]
        else:
            main_score = score

        main_score = main_score.strip()

        if "–" in main_score:
            home_score, away_score = main_score.split("–")
        elif "-" in main_score:
            # Fallback to regular hyphen if en dash not found
            home_score, away_score = main_score.split("-")
        else:
            print(f"Warning: Could not parse score: '{score}'")
            home_score, away_score = "", ""

        home_scores.append(home_score)
        away_scores.append(away_score)
        print(home_scores, "  ", away_scores)

    return home_scores, away_scores


def fill_and_convert_columns(df):
    if "df" in locals() and not df.empty:
        # Add match_id column
        df["match_id"] = range(1, len(df) + 1)

        # Add new columns
        # Pandas is smart enough to "broadcast" this single value to every row.
        df["league"] = "Premier League"
        df["season"] = "2024-2025"

        # Convert the score column to home_score and away_score, then add the 2 columns to df
        df["home_score"], df["away_score"] = convert_score_to_home_score_and_away_score(
            df["score"]
        )

        df["source"] = "fbref.com"

        print("\nSuccess! DataFrame after adding new columns:\n")
        print(df.head())

    else:
        print(
            "DataFrame 'df' not found or is empty. Please run the parsing step first."
        )

    # Drop the score column
    df = df.drop(columns="score")

    return df


def create_csv(df, filepath):
    # Save the dataframe to CSV

    # index=False to avoid writing row numbers to the CSV
    df.to_csv(filepath, index=False)


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
