"""
FBref collector utilities used by scripts/collect_all.py.

This module intentionally avoids hard Selenium dependencies in order to keep
setup simple. The `download_with_selenium` function provides a lightweight
requests-based fallback with a clear warning about bot protection.
"""

import os
import re
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

# -------- Paths (resolved relative to this file) --------


def _here() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_data_raw_folder() -> str:
    """Absolute path to data-collection/data/raw."""
    p = os.path.join(_here(), "..", "data", "raw")
    return os.path.normpath(p)


def get_data_processed_folder() -> str:
    """Absolute path to data-collection/data/processed."""
    p = os.path.join(_here(), "..", "data", "processed")
    return os.path.normpath(p)


# -------- URL generation --------


def generate_fbref_url(league_id: int, league_name: str, season: int) -> str:
    """
    Generate an FBref schedule/results URL.

    ex, Premier League (id=9):
        https://fbref.com/en/comps/9/2024-2025/schedule/Premier-League-Scores-and-Fixtures
    """
    season_span = f"{season}-{season+1}"
    # Ensure league_name has dashes instead of spaces
    league_slug = league_name.replace(" ", "-")
    return f"https://fbref.com/en/comps/{league_id}/{season_span}/schedule/{league_slug}-Scores-and-Fixtures"


def save_html_to_file(html: str, output_file: str) -> str:
    """Save HTML to data/raw/<output_file> and return full path."""
    raw_dir = get_data_raw_folder()
    os.makedirs(raw_dir, exist_ok=True)
    path = os.path.join(raw_dir, output_file)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def extract_columns(soup, data_fields: list[str], html_filepath: str) -> pd.DataFrame:
    """Extract specified columns from HTML using BeautifulSoup."""
    parsed_rows = []
    # Find the specific table we care about using BeautifulSoup
    table = soup.find("table", class_="stats_table")

    if table:
        for row in table.find("tbody").find_all("tr"):
            # Find the specific cells '<td>' by their 'data-stat' attribute
            fields = {"date": "", "score": "", "home_team": "", "away_team": ""}
            for field in fields:
                # Find the specific cells '<td>' by their 'data-stat' attribute
                cell = row.find("td", {"data-stat": field})
                # Extract the text from each cell, checking if the cell was found
                fields[field] = cell.text.strip() if cell else ""

            # Create a dictionary for each row
            parsed_rows.append(fields)

    # Convert our list of dictionaries into a pandas DataFrame
    if parsed_rows:
        # 2nd arg preserves the order of the columns
        df_bs = pd.DataFrame(
            parsed_rows, columns=["date", "score", "home_team", "away_team"]
        )
        print("\nSuccess! Extracted columns using BeautifulSoup:\n")
    else:
        print("\nFailed to extract columns using BeautifulSoup.")

    return df_bs


def add_new_columns_to_fbref(df: pd.DataFrame, file) -> pd.DataFrame:
    # Fill in match_id column
    df["match_id"] = range(len(df))
    # Split score into home_score and away_score
    df["home_score"], df["away_score"] = convert_score_to_home_score_and_away_score(
        df["score"]
    )

    tmp = file.split("_")
    df["league"] = tmp[1]
    df["season"] = tmp[2].split(".")[0]
    df["source"] = tmp[0]

    return df


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

    return home_scores, away_scores


def normalize_date(df: pd.DataFrame) -> pd.DataFrame:
    # Best-effort date normalization (expects day/month/year or ISO)
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
        except Exception:
            pass

    return df


def reorder_df(df):
    # Get specified columns and reorder them
    df_processed = get_columns(
        df,
        "match_id",
        "date",
        "league",
        "season",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "source",
    )

    return df_processed


# The *arg syntax in Python automatically packs the extra positional arguments into a tuple by default.
def get_columns(df, *args) -> pd.DataFrame:
    """Dynamic column selection"""
    valid_cols = [col for col in args if col in df.columns]
    return df[valid_cols]


def create_csv(df: pd.DataFrame, filename: str) -> str:
    """Save DataFrame to CSV under data/processed/filename"""

    filepath = os.path.join(get_data_processed_folder(), filename)

    # If output_path is not absolute, write under processed folder
    if not os.path.isabs(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Processed CSV saved as '{filepath}'.")
    return filepath


def download_with_selenium(url):
    # Why use Selenium?

    # (1) BeautifulSoup is great for static HTML, but if the page loads content dynamically, we need Selenium.
    #     - Many modern websites dynamically load content using JavaScript, meaning some elements (like tables, buttons, or text) are not present in the initial HTML source when you request the page using requests or BeautifulSoup.
    #     - Instead, the page executes JavaScript to fetch and display the content after the page has initially loaded.

    # (2) Uses Selenium WebDriver to bypass JavaScript-based bot detection (like Cloudflare).

    # (3) Selenium simulates a real user's behavior, making it harder for websites to detect automated requests.

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
