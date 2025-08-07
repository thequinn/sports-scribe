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
from datetime import datetime
import requests
import pandas as pd


def generate_request_url(league_id, league_name, season):
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


def get_data_raw_folder():
    # Get the cur script dir for .py
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate to the data/raw, and clean up the path
    data_raw_folder = os.path.join(cur_dir, "..", "data", "raw")
    data_raw_folder = os.path.normpath(data_raw_folder)

    return data_raw_folder


def get_data_processed_folder():
    # Get the cur script dir for .py
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate to the data/processed, and clean up the path
    data_processed_folder = os.path.join(cur_dir, "..", "data", "processed")
    data_processed_folder = os.path.normpath(data_processed_folder)

    return data_processed_folder


def download_csv(url: str, filename: str = "data.csv"):
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

    # Build the full filepath
    filepath = get_data_raw_folder() + filename

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        # print("Request successful:", response.status_code)
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch data from {url}. Error: {e}")

    # Write to data/raw/filename
    with open(filepath, "wb") as f:
        f.write(response.content)
    print(f"Raw CSV saved as '{filepath}'.")


def read_csv(filename: str) -> pd.DataFrame:
    """Read CSV file into pandas DataFrame."""
    filepath = get_data_raw_folder() + filename

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


def get_columns(df, *args) -> pd.DataFrame:
    """Dynamic column selection"""
    valid_cols = [col for col in args if col in df.columns]
    return df[valid_cols]


def get_league_name_from_file(file):
    """Extract league name from filename."""
    # ex. E0_2024.csv => Premier-League
    league_name = file.split("_")[0]
    print("League name from filename: {league_name}")
    return league_name


def add_new_columns(df_clean, file):
    """Add new columns to df_clean."""
    df_clean["match_id"] = df_clean.index
    df_clean["league"] = get_league_name_from_file(file)
    df_clean["season"] = file.split("_")[1].split(".")[0]
    df_clean["source"] = "football-data.co.uk"
    return df_clean


def process_df(df):
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


def save_df_to_csv(df, raw_filename):
    """Save DataFrame to CSV."""

    processed_filename = raw_filename.split(".")[0] + "_processed.csv"
    filepath = get_data_processed_folder() + processed_filename
    df.to_csv(filepath, index=False)
    print(f"Processed CSV saved as '{filepath}'.")


# def read_and_concat_csvs():
#     data_processed_folder = get_data_processed_folder()

#     # Get all CSV files in the data/raw folder
#     csv_files = [f for f in os.listdir(data_raw_folder) if f.endswith(".csv")]
#     # print(csv_files)

#     # Read each CSV into a DataFramea, clean it and store the cleaned data to a new .csv file.
#     for file in csv_files:
#         path = os.path.join(data_raw_folder, file)
#         print(f"path: {path}")

#         df = pd.read_csv(path)

#         # Rename columns to match our schema
#         df = rename_columns(df)

#         # Add new columns to df
#         df["match_id"] = df.index
#         df["league"] = get_league_name_from_file(file)
#         # Extract season from filename, E0_2024.csv => 2024
#         df["season"] = file.split("_")[1].split(".")[0]
#         df["source"] = "football-data.co.uk"

#         # Ensures the folder exists without throwing an error
#         # os.makedirs("data/processed", exist_ok=True)

#         # Write the cleaned DataFrame to a new CSV file
#         output_file = file.replace(".csv", "") + "_processed.csv"

#         # Navigate to the data/processed, and clean up the path
#         data_processed_folder = os.path.join(cur_dir, "..", "data", "processed")
#         data_processed_folder = os.path.normpath(data_processed_folder)

#         output_path = os.path.join(data_processed_folder, output_file)

#         df_clean.to_csv(output_path, index=False)
#         print(f"Cleaned CSV saved as '{output_path}'.")


# if __name__ == "__main__":
#     season = 2024
#     season_code = f"{str(season)[-2:]}{str(season+1)[-2:]}"
#     league_code = "E0"  # Premier League

#     base_url = "https://www.football-data.co.uk/mmz4281"
#     url = f"{base_url}/{season_code}/{league_code}.csv"
#     new_filename = f"{league_code}_{season}.csv"

#     download_csv(url, new_filename, overwrite=True)
