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


example row from .csv file:

Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HTHG,HTAG,HTR,Referee,HS,AS,HST AST,HF,AF,HC,AC,HY,AY,HR,AR,B365H,B365D,B365A,BWH,BWD,BWA,BFH,BFD,BFA,PSH,PSD,PSA,WHH,WHD,WHA,1XBH,1XBD,1XBA,MaxH,MaxD,MaxA,AvgH,AvgD,AvgA,BFEH,BFED,BFEA,B365>2.5,B365<2.5,P>2.5,P<2.5,Max>2.5,Max<2.5,Avg>2.5,Avg<2.5,BFE>2.5,BFE<2.5,AHh,B365AHH,B365AHA,PAHH,PAHA,MaxAHH,MaxAHA,AvgAHH,AvgAHA,BFEAHH,BFEAHA,B365CH,B365CD,B365CA,BWCH,BWCD,BWCA,BFCH,BFCD,BFCA,PSCH,PSCD,PSCA,WHCH,WHCD,WHCA,1XBCH,1XBCD,1XBCA,MaxCH,MaxCD,MaxCA,AvgCH,AvgCD,AvgCA,BFECH,BFECD,BFECA,B365C>2.5,B365C<2.5,PC>2.5,PC<2.5,MaxC>2.5,MaxC<2.5,AvgC>2.5,AvgC<2.5,BFEC>2.5,BFEC<2.5,AHCh,B365CAHH,B365CAHA,PCAHH,PCAHA,MaxCAHH,MaxCAHA,AvgCAHH,AvgCAHA,BFECAHH,BFECAHA

E0,16/08/2024,20:00,Man United,Fulham,1,0,H,0,0,D,R Jones,14,10,5,2,12,10,7,8,2,3,0,0,1.6,4.2,5.25,1.6,4.4,5.25,1.6,4.33,5,1.63,4.38,5.3,1.65,4.2,5,1.68,4.32,5.03,1.68,4.5,5.5,1.62,4.36,5.15,1.66,4.5,5.6,1.53,2.5,1.56,2.56,1.57,2.6,1.53,2.52,1.59,2.64,-1,2.05,1.88,2.07,1.86,2.07,1.89,2.03,1.85,2.1,1.88,1.67,4.1,5,1.65,4.2,4.8,1.62,4,5,1.65,4.23,5.28,1.6,4.2,5.5,1.66,4.15,5.33,1.7,4.33,5.5,1.66,4.2,5.02,1.72,4.2,5.4,1.62,2.3,1.63,2.38,1.66,2.45,1.61,2.37,1.68,2.46,-0.75,1.86,2.07,1.83,2.11,1.88,2.11,1.82,2.05,1.9,2.08

"""

import sys
import os
from bs4 import BeautifulSoup

# Add the data-collection directory to the Python path
data_collection_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print("data_collection dir:", data_collection_dir)
sys.path.append(data_collection_dir)

from collectors.football_data_collector import download_csv, read_and_concat_csvs
from collectors.fbref_collector import (
    convert_score_to_home_score_and_away_score,
    download_with_selenium,
    extract_columns,
    fill_columns,
    generate_request_url,
    save_html_to_file,
    create_csv,
)


# Data Requirements:
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


if __name__ == "__main__":
    # Collecting data from football-data.co.uk

    # Premier League, Champions League (Le Championnat d'Europe), La Liga
    # leagues = ["E0", "SP1", "F1"]
    # seasons = [2024, 2023, 2022, 2021, 2020]  # Last 5 seasons
    """
    leagues = ["F1"]
    seasons = [2024, 2023]

    for league in leagues:
        for season in seasons:
            season_code = f"{str(season)[-2:]}{str(season+1)[-2:]}"
            base_url = "https://www.football-data.co.uk/mmz4281"
            url = f"{base_url}/{season_code}/{league}.csv"
            new_filename = f"{league}_{season}.csv"
            download_csv(url, new_filename, overwrite=True)
    print("\n")

    read_and_concat_csvs()
    print("\n")
    """

    """
    # Collecting data from fbref.com
    print(
        "\nfbfre.com has strong bot protection, requests method is not reliable. Using Selenium method only..."
    )
    """
    """
    league_ids = [9, 8, 12]  # Premier League, Champions League, La Liga
    league_names = ["Premier-League", "Champions-League", "La-Liga"]
    seasons= [2020, 2021, 2022, 2023, 2024]
    """
    """
    league_ids = [8]  # Premier League, Champions League, La Liga
    league_names = ["Champions-League"]
    seasons = [2024]

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

    ##################
    # Scraping/Extracting the essential fields for DB
    # extract_elements(soup, data_fields)
    extract_columns(soup, data_fields, html_filepath)
    print(".......")

    """
    extracted_data = {}
    for data_field in data_fields:
        print(f"Extracting {data_field}...")
        extracted_data[data_field] = extract_elements(soup, data_field)
        print(f"Extracted {data_field}:")
        print(extracted_data[data_field])
    """
"""
    # Rename field names to match our schema
    # Todo: allow dynamic league names, seasons
    extracted_data = fill_columns(extracted_data)

    # Convert score to home_score and away_score
    convert_score_to_home_score_and_away_score(extracted_data)

    # Remove score field
    extracted_data.pop("score", None)

    csv_filename = html_filename.split(".")[0] + ".csv"
    data_processed_folder = os.path.join(cur_dir, "..", "data", "processed")
    data_processed_folder = os.path.normpath(data_processed_folder)

    csv_filename = os.path.join(data_processed_folder, csv_filename)
    print("data/processes/csv_filename:", csv_filename)

    create_csv(extracted_data, csv_filename)
"""
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
