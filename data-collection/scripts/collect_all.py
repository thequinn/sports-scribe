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

# Add the data-collection directory to the Python path
data_collection_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print("data_collection dir:", data_collection_dir)
sys.path.append(data_collection_dir)

from collectors.football_data_collector import download_csv, read_and_concat_csvs

if __name__ == "__main__":
    # Premier League, La Liga League
    # leagues = ["E0", "SP1"]
    # seasons = [2024, 2023, 2022, 2021, 2020]  # Last 5 seasons
    #
    """
    For testing purposes, only download 1 season and 1 league
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
