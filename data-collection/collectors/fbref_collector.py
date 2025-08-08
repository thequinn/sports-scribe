"""
FBref collector utilities used by scripts/collect_all.py.

This module intentionally avoids hard Selenium dependencies in order to keep
setup simple. The `download_with_selenium` function provides a lightweight
requests-based fallback with a clear warning about bot protection.
"""

import os
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException


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
        except Exception as e:
            print("Failed to normalize date")
            print(e)

    return df


def reorder_df_fbref(df):
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


def _configure_chrome_options() -> Options:
    """Create and return a configured Chrome Options object."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument('--headless')  # Optional: enable headless mode

    # User agent to mimic real browser
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Set Chrome binary location for macOS if available
    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin
    return chrome_options


def _create_driver(chrome_options: Options):
    """Initialize and return a Chrome WebDriver instance."""
    print("Starting Chrome WebDriver...")
    return webdriver.Chrome(options=chrome_options)


def _remove_webdriver_flag(driver) -> None:
    """Mask the webdriver flag to reduce detection."""
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )


def _wait_out_challenge(driver, timeout: int = 30) -> None:
    """Wait for common anti-bot challenge pages to clear, within timeout."""
    print("Waiting for page to load and any challenges to complete...")
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: "Just a moment" not in d.title
            and "Checking your browser" not in d.page_source
        )
        print("Challenge completed or page loaded successfully.")
    except TimeoutException:
        print("Timeout waiting for challenge completion, but proceeding anyway...")


def _get_html_or_raise(driver) -> str:
    """Return page HTML or raise if a challenge page is still present."""
    html_content = driver.page_source
    if "Just a moment" in html_content or "Checking your browser" in html_content:
        raise ValueError("Still showing Cloudflare challenge page")
    return html_content


def download_with_selenium(url):
    """Fetch dynamic page content using Selenium and return HTML (<=50 lines)."""
    driver = None
    try:
        options = _configure_chrome_options()
        driver = _create_driver(options)
        _remove_webdriver_flag(driver)

        print(f"Navigating to {url} ...")
        driver.get(url)

        _wait_out_challenge(driver, timeout=30)
        time.sleep(random.uniform(2, 5))  # small buffer to ensure full render

        html_content = _get_html_or_raise(driver)
        print("Successfully retrieved page.")
        return html_content

    except WebDriverException as e:
        print(f"WebDriver error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome browser is installed")
        print("2. Install ChromeDriver: brew install --cask chromedriver")
        print("3. Or use: pip install webdriver-manager")
        raise ValueError(f"WebDriver error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise ValueError(f"Failed to scrape with Selenium: {e}")

    finally:
        if driver:
            print("Closing browser...")
            driver.quit()
