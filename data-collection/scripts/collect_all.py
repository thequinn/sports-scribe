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
"""

import sys
import os

# Add the data-collection directory to the Python path
data_collection_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print("data_collection dir:", data_collection_dir)
sys.path.append(data_collection_dir)

from bs4 import BeautifulSoup
from collectors.football_data_collector import (
    add_new_columns_to_football_data,
    download_csv,
    generate_football_data_url,
    reorder_df_football_data,
    read_csv,
    rename_columns,
    save_df_to_csv,
)
from collectors.fbref_collector import (
    generate_fbref_url,
    download_with_selenium,
    extract_columns,
    add_new_columns_to_fbref,
    reorder_df_fbref,
    normalize_date,
    create_csv,
    save_html_to_file,
)

resources = {0: "football-data", 1: "fbref.com", 2: "whoscored.com"}

# Essential data fields:
# Note: the fields commented out will be filled during data processing
data_fields = [
    # "match_id",
    "date",
    # "league",
    # "season",
    "home_team",
    "away_team",
    "score",
    # "home_score",
    # "away_score",
    # "source",
]

"""
# Todo: Add additional data fields: (Optional)
  - referee, attendance, venue
  - half_time_scores
  - basic_statistics (shots, possession)
"""


def get_data_folder():
    # Get the cur script dir for .py
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate to the data/raw, and clean up the path
    data_raw_folder = os.path.join(cur_dir, "..", "data")
    data_raw_folder = os.path.normpath(data_raw_folder)

    return data_raw_folder


if __name__ == "__main__":

    print("Collecting data from football-data.co.uk...\n")

    # Premier League, Champions League (Le Championnat d'Europe), La Liga
    leagues = [{"E0": "Premier-League"}, {"SP1": "La-Liga"}, {"F1": "Champions-League"}]
    seasons = [2024, 2023, 2022, 2021, 2020]  # Last 5 seasons

    # Flatten the list of dictionaries, leagues
    # ex. leagues_flat = [("E0": "Premier League"), ("SP1": "La Liga")]
    leagues_flat = [(k, v) for league in leagues for k, v in league.items()]
    print(
        "Flattened leagues[]:",
        leagues_flat,
    )

    for league_code, league_name in leagues_flat:
        for season in seasons:
            url = generate_football_data_url(league_code, league_name, season)

            # Download the CSV file and rename it
            raw_csv_filename = f"{resources[0]}_{league_name}_{season}.csv"
            download_csv(url, raw_csv_filename)

            # Read the CSV file into a pandas DataFrame
            df_raw = read_csv(raw_csv_filename)

            # Clean and process the data
            df_cleaned = rename_columns(df_raw)
            df_cleaned = add_new_columns_to_football_data(df_cleaned, raw_csv_filename)
            df_cleaned = reorder_df_football_data(df_cleaned)
            df_cleaned = normalize_date(df_cleaned)
            print(df_cleaned.head())

            # Save the processed data to a new CSV file
            df_cleaned = save_df_to_csv(df_cleaned, raw_csv_filename)
    print("\n- - - - - - - - - - - - - - - - - - - - - - -\n")

    print("Collecting data from fbref.com...\n")
    print(
        "fbfre.com has strong bot protection, requests method is not reliable. Using Selenium method only..."
    )

    league_ids = [9, 8, 12]  # Premier League, Champions League, La Liga
    league_names = ["Premier-League", "Champions-League", "La-Liga"]
    seasons = [2020, 2021, 2022, 2023, 2024]

    for season in seasons:
        for league_id, league_name in zip(league_ids, league_names):
            url = generate_fbref_url(league_id, league_name, season)
            html_content = download_with_selenium(url)

            # Save the downloadedHTML content to a file for inspection
            html_filename = f"fbref_{league_name}_{season}.html"
            save_html_to_file(html_content, html_filename)

            # Read the html file into BeautfulSoup object
            html_filepath = get_data_folder() + "/raw/" + html_filename
            try:
                with open(html_filepath, "r", encoding="utf-8") as f:
                    html_content = f.read()
                soup = BeautifulSoup(html_content, "lxml")
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                print(f"Error reading file: {e}")
                # Return an empty soup as fallback
                soup = BeautifulSoup("", "lxml")

            # Scraping/Extracting the essential fields for DB
            df = extract_columns(soup, data_fields, html_filename)

            # Clean and process the data
            df_cleaned = add_new_columns_to_fbref(df, html_filename)
            df_cleaned = reorder_df_fbref(df_cleaned)
            df_cleaned = normalize_date(df_cleaned)

            csv_filename = html_filename.split(".")[0] + "_processed.csv"
            create_csv(df_cleaned, csv_filename)
