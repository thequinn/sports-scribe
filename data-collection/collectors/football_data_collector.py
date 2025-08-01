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
import requests


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
    - FileExistsError: If the file exists and overwrite is False.
    """
    # Ensure the data/raw directory exists
    os.makedirs("data/raw", exist_ok=True)

    # Build the full filepath
    filepath = os.path.join("data", "raw", filename)

    if not overwrite and os.path.exists(filepath):
        raise FileExistsError(
            f"'{filepath}' already exists. Set overwrite=True to replace it."
        )

    response = requests.get(url)

    if response.status_code != 200:
        raise ValueError(f"Failed to fetch data. Status code: {response.status_code}")

    # Write to data/raw/filename
    with open(filepath, "wb") as f:
        f.write(response.content)

    print(f"CSV saved as '{filepath}'.")


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
