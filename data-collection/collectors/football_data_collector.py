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

import os
import requests
import pandas as pd


def generate_football_data_url(league_id, league_name, season):
    """
    Generate url based on league and season.

    ex. Premier League 2024-2025
        https://www.football-data.co.uk/mmz4281/2425/E0.csv

    ex. Champions League 2023-2024
        https://www.football-data.co.uk/mmz4281/2425/E1.csv

    ex. La Liga 2023-2024
        https://www.football-data.co.uk/mmz4281/2425/SP1.csv

    Explanation of the URL structure:
    https://www.football-data.co.uk/mmz4281/{season_code}/{league_code}.csv

      • mmz4281 is the root folder for season data.
      • {season_code} like 2425 refers to the 2024–2025 season.
      • {league_code} like E0 refers to the Premier League.
    """
    season_code = f"{str(season)[-2:]}{str(season+1)[-2:]}"
    base_url = "https://www.football-data.co.uk/mmz4281"
    url = base_url + f"/{season_code}/{league_id}.csv"
    return url


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


def download_csv(url: str, filename: str = "football-data_data.csv"):
    """
    Fetches a CSV file from the specified URL and saves it locally.

    Parameters:
    - url (str): The URL pointing to the CSV file.
    - filename (str): Desired name for the saved file. Defaults to 'data.csv'.
    - overwrite (bool): Whether to overwrite existing file. Defaults to False.

    Raises:
    - ValueError: If the response status is not 200 (OK).
    - FileExistsError: If the file exists and overwrite is False
    """

    filepath = os.path.join(get_data_raw_folder(), filename)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch data from {url}. Error: {e}")

    # Write to data/raw/filename
    with open(filepath, "wb") as f:
        f.write(response.content)
    print(f"Raw CSV saved as {filepath}\n")


def read_csv(filename: str) -> pd.DataFrame:
    """Read CSV file into pandas DataFrame."""
    data_raw_folder = get_data_raw_folder()
    filepath = os.path.join(data_raw_folder, filename)
    return pd.read_csv(filepath)


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to match our schema."""
    column_mapping = {
        "Date": "date",
        "HomeTeam": "home_team",
        "AwayTeam": "away_team",
        "FTHG": "home_score",
        "FTAG": "away_score",
    }
    return df.rename(columns=column_mapping)


def add_new_columns_to_football_data(df_clean, file):
    """Add new columns to df_clean."""
    df_clean["match_id"] = df_clean.index

    tmp = file.split("_")
    df_clean["league"] = tmp[1]
    df_clean["season"] = tmp[2].split(".")[0]
    df_clean["source"] = tmp[0]
    return df_clean


# The *arg syntax in Python automatically packs the extra positional arguments into a tuple by default.
def get_columns(df, *args) -> pd.DataFrame:
    """Dynamic column selection"""
    valid_cols = [col for col in args if col in df.columns]
    return df[valid_cols]


def reorder_df_football_data(df):
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
    print("After getting essential columns:")
    print(df_processed.head())
    print("df_processed.columns:", df_processed.columns)
    return df_processed


def normalize_date(df: pd.DataFrame) -> pd.DataFrame:
    # Best-effort date normalization (expects day/month/year or ISO)
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
        except Exception as e:
            print("Failed to normalize date")
            print(e)

    return df


def save_df_to_csv(df, raw_filename):
    """Save DataFrame to CSV"""
    processed_filename = raw_filename.split(".")[0] + "_processed.csv"
    filepath = os.path.join(get_data_processed_folder(), processed_filename)
    df.to_csv(filepath, index=False)
    print(f"Processed CSV saved as '{filepath}'.")
