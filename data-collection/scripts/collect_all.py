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
from bs4 import BeautifulSoup

# Add the data-collection directory to the Python path
data_collection_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print("data_collection dir:", data_collection_dir)
sys.path.append(data_collection_dir)

from collectors.football_data_collector import (
    add_new_columns,
    download_csv,
    # read_and_concat_csvs,
    generate_request_url as generate_football_data_url,
    process_df,
    read_csv,
    rename_columns,
    save_df_to_csv,
)
from collectors.fbref_collector import (
    convert_score_to_home_score_and_away_score,
    download_with_selenium,
    extract_columns,
    fill_and_convert_columns,
    generate_request_url as generate_fbref_url,
    save_html_to_file,
    create_csv,
)

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


if __name__ == "__main__":

    print("Collecting data from football-data.co.uk...\n")

    # Premier League, Champions League (Le Championnat d'Europe), La Liga
    # leagues = [{"E0": "Premier-League"}, {"SP1": "La-Liga"}, {"F1": "Champions-League"}]
    # seasons = [2024, 2023, 2022, 2021, 2020]  # Last 5 seasons

    leagues = [{"E0": "Premier-League"}]
    seasons = [2024]

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
            raw_csv_filename = f"{league_name}_{season}.csv"
            download_csv(url, raw_csv_filename)
            df_raw = read_csv(raw_csv_filename)
            print("df_raw.head():", df_raw.head())
            print("df_raw.columns:", df_raw.columns)

            # Rename columns to match our schema
            df_cleaned = rename_columns(df_raw)
            df_cleaned = add_new_columns(df_cleaned, raw_csv_filename)
            df_processed = process_df(df_cleaned)
            df_processed = save_df_to_csv(df_processed, raw_csv_filename)
    print("\n")

    # read_and_concat_csvs()
    # print("\n")

    # print("Collecting data from fbref.com...\n")
    # print(
    #     "\nfbfre.com has strong bot protection, requests method is not reliable. Using Selenium method only..."
    # )

    # league_ids = [9, 8, 12]  # Premier League, Champions League, La Liga
    # league_names = ["Premier-League", "Champions-League", "La-Liga"]
    # seasons = [2020, 2021, 2022, 2023, 2024]

    # league_ids = [8]  # Premier League, Champions League, La Liga
    # league_names = ["Champions-League"]
    # seasons = [2024]

    # try:
    #     for season in seasons:
    #         for league_id, league_name in zip(league_ids, league_names):
    #             url = generate_request_url(league_id, league_name, season)
    #             print(f"\nGenerated URL: {url}")

    #             html_content = download_with_selenium(url)
    #         print("Success with Selenium method!")

    #         # Save the HTML content to a file for inspection
    #         output_file = f"fbref_{league_name}_{season}_{season+1}.html"
    #     save_html_to_file(html_content, output_file)

    # except ValueError as selenium_error:
    #     print(f"\nSelenium method also failed: {selenium_error}")
    #     print("\nBoth methods failed. This site has strong bot protection.")

"""
    # Add code to extract data from the downloaded .html for quick testing purpose
    # TODO: handle all 5 seasons data
    cur_dir = os.path.dirname((os.path.abspath(__file__)))

    html_filename = "fbref_Premier-League_2024_2025.html"
    data_raw_folder = os.path.join(cur_dir, "..", "data", "raw")
    data_raw_folder = os.path.normpath(data_raw_folder)

    html_filepath = os.path.join(data_raw_folder, html_filename)
    print("data/raw/html_filepath:", html_filepath)

    try:
        with open(html_filepath, "r", encoding="utf-8") as f:
            html_content = f.read()
            # print("HTML content loaded from file.")
            # print(f"html_content: {html_content}")
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        print(f"Error reading file: {e}")
        html_content = ""  # Or handle fallback

    # Assuming 'html_content' is the variable holding your downloaded HTML
    soup = BeautifulSoup(html_content, "lxml")

    # Scraping/Extracting the essential fields for DB
    df = extract_columns(soup, data_fields, html_filepath)

    df = fill_and_convert_columns(df)
    print("After filling columns:")
    print(df.iloc[0])

    csv_filename = html_filename.split(".")[0] + ".csv"
    data_processed_folder = os.path.join(cur_dir, "..", "data", "processed")
    data_processed_folder = os.path.normpath(data_processed_folder)

    csv_filename = os.path.join(data_processed_folder, csv_filename)
    print("data/processes/csv_filename:", csv_filename)

    # Reorder columns based on the essential fields specified on PRD
    df = df[
        [
            "match_id",
            "date",
            "league",
            "season",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "source",
        ]
    ]

    create_csv(df, csv_filename)
"""
