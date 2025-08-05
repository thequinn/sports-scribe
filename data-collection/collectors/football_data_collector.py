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


📅 Daily Sprint Plan -> Day 1 (Monday): Setup & Premier League
https://realityai.notion.site/Sports-Scribe-21c456247e0a802085faccfd667558a0
"""

import os
from datetime import datetime
import requests
import pandas as pd

"""
essential fields: (Must have)
  - match_id, date, league, season
  - home_team, away_team
  - home_score, away_score
  - source

Field mapping between our schema and the CSV fields:
  match_id: Referee
  home_team: HomeTeam
  away_team: AwayTeam
  home_score: FTHG
  away_score: FTAG
  source: football-data.co.uk
"""


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


def get_columns(df, *args) -> pd.DataFrame:
    """Dynamic column selection"""
    valid_cols = [col for col in args if col in df.columns]
    return df[valid_cols]


def read_and_concat_csvs():
    # Get the cur script dir for .py
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate to the data/raw, and clean up the path
    data_raw_folder = os.path.join(cur_dir, "..", "data", "raw")
    data_raw_folder = os.path.normpath(data_raw_folder)

    # Get all CSV files in the data/raw folder
    csv_files = [f for f in os.listdir(data_raw_folder) if f.endswith(".csv")]
    # print(csv_files)

    # Read each CSV into a DataFramea, clean it and store the cleaned data to a new .csv file.
    for file in csv_files:
        path = os.path.join(data_raw_folder, file)
        print(f"path: {path}")

        df = pd.read_csv(path)

        # Rename columns to match our schema
        df = rename_columns(df)

        df["match_id"] = df.index
        df["league"] = "Premier League"
        # Extract season from filename, E0_2024.csv => 2024
        df["season"] = file.split("_")[1].split(".")[0]
        df["source"] = "football-data.co.uk"

        # Get specified columns
        df_clean = get_columns(
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
        print("After getting essentialcolumns:")
        print(df_clean.head())

        # Ensures the folder exists without throwing an error
        # os.makedirs("data/processed", exist_ok=True)

        # Write the cleaned DataFrame to a new CSV file
        output_file = file.replace(".csv", "") + "_cleaned.csv"

        # Navigate to the data/processed, and clean up the path
        data_processed_folder = os.path.join(cur_dir, "..", "data", "processed")
        data_processed_folder = os.path.normpath(data_processed_folder)

        output_path = os.path.join(data_processed_folder, output_file)

        df_clean.to_csv(output_path, index=False)
        print(f"Cleaned CSV saved as '{output_path}'.")


def download_csv(url: str, filename: str = "data.csv", overwrite: bool = False):
    """
    Fetches a CSV file from the specified URL and saves it locally.

    Example link to download csv data for premier league 2024-25
    https://www.football-data.co.uk/mmz4281/2425/E0.csv


    Explanation of the URL structure:
    https://www.football-data.co.uk/mmz4281/{season_code}/{league_code}.csv

      • mmz4281 is the root folder for season data.
      • {season_code} like 2324 refers to the 2023–2024 season.
      • {league_code} like E0 refers to the Premier League.


    Parameters:
    - url (str): The URL pointing to the CSV file.
    - filename (str): Desired name for the saved file. Defaults to 'data.csv'.
    - overwrite (bool): Whether to overwrite existing file. Defaults to False.

    Raises:
    - ValueError: If the response status is not 200 (OK).
    - FileExistsError: If the file exists and overwrite is False
    """

    # Build absolute path to data/raw folder
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    data_raw_folder = os.path.join(cur_dir, "..", "data", "raw")

    # Alternative: Use os.path.normpath to clean up the path
    data_raw_folder = os.path.normpath(data_raw_folder)

    # Build the full filepath
    filepath = os.path.join(data_raw_folder, filename)

    if not overwrite and os.path.exists(filepath):
        raise FileExistsError(
            f"'{filepath}' already exists. Set overwrite=True to replace it."
        )

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        # print("Request successful:", response.status_code)
    except requests.exceptions:
        raise ValueError(f"Failed to fetch data. Status code: {response.status_code}")

    # Write to data/raw/filename
    with open(filepath, "wb") as f:
        f.write(response.content)
    print(f"Raw CSV saved as '{filepath}'.")


"""
if __name__ == "__main__":
    season = 2024
    season_code = f"{str(season)[-2:]}{str(season+1)[-2:]}"
    league_code = "E0"  # Premier League

    base_url = "https://www.football-data.co.uk/mmz4281"
    url = f"{base_url}/{season_code}/{league_code}.csv"
    new_filename = f"{league_code}_{season}.csv"

    download_csv(url, new_filename, overwrite=True)
"""
