#!/usr/bin/env python3
"""
Sport Scribe - Database Seed Script
Seeds sample data for development and testing
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List

# Add the shared directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

try:
    import structlog
    from supabase import Client, create_client
except ImportError:
    print("❌ Required packages not installed. Run: pip install supabase structlog")
    sys.exit(1)

# Setup logging
logger = structlog.get_logger()

# Sample data
SAMPLE_TEAMS = [
    {
        "name": "Manchester United",
        "city": "Manchester",
        "sport": "football",
        "league": "Premier League",
    },
    {
        "name": "Manchester City",
        "city": "Manchester",
        "sport": "football",
        "league": "Premier League",
    },
    {
        "name": "Liverpool",
        "city": "Liverpool",
        "sport": "football",
        "league": "Premier League",
    },
    {
        "name": "Arsenal",
        "city": "London",
        "sport": "football",
        "league": "Premier League",
    },
    {"name": "Real Madrid", "city": "Madrid", "sport": "football", "league": "La Liga"},
    {
        "name": "Barcelona",
        "city": "Barcelona",
        "sport": "football",
        "league": "La Liga",
    },
]

SAMPLE_PLAYERS = [
    {"name": "Marcus Rashford", "position": "LW", "team_id": 1, "jersey_number": 10},
    {"name": "Bruno Fernandes", "position": "CAM", "team_id": 1, "jersey_number": 8},
    {"name": "Erling Haaland", "position": "ST", "team_id": 2, "jersey_number": 9},
    {"name": "Kevin De Bruyne", "position": "CM", "team_id": 2, "jersey_number": 17},
    {"name": "Mohamed Salah", "position": "RW", "team_id": 3, "jersey_number": 11},
    {"name": "Virgil van Dijk", "position": "CB", "team_id": 3, "jersey_number": 4},
    {"name": "Bukayo Saka", "position": "RW", "team_id": 4, "jersey_number": 7},
    {"name": "Martin Ødegaard", "position": "CAM", "team_id": 4, "jersey_number": 8},
]

SAMPLE_GAMES = [
    {
        "home_team_id": 1,
        "away_team_id": 2,
        "game_date": datetime.now() - timedelta(days=1),
        "home_score": 2,
        "away_score": 1,
        "status": "completed",
        "venue": "Old Trafford",
    },
    {
        "home_team_id": 3,
        "away_team_id": 4,
        "game_date": datetime.now() + timedelta(days=7),
        "home_score": None,
        "away_score": None,
        "status": "scheduled",
        "venue": "Anfield",
    },
    {
        "home_team_id": 5,
        "away_team_id": 6,
        "game_date": datetime.now() + timedelta(days=14),
        "home_score": None,
        "away_score": None,
        "status": "scheduled",
        "venue": "Santiago Bernabéu",
    },
]

SAMPLE_ARTICLES = [
    {
        "title": "Manchester United Edge Past City in Thrilling Derby Victory",
        "content": "In a spectacular display of tactical brilliance and individual quality, Manchester United defeated Manchester City 2-1 in a pulsating Manchester Derby at Old Trafford. Marcus Rashford opened the scoring with a sublime finish before Erling Haaland equalized for City. Bruno Fernandes sealed the victory with a penalty in the 78th minute, sending the home crowd into raptures...",
        "summary": "Manchester United beat Manchester City 2-1 in thrilling Manchester Derby",
        "author": "AI Sports Writer",
        "status": "published",
        "tags": [
            "football",
            "Premier League",
            "Manchester United",
            "Manchester City",
            "Derby",
        ],
        "game_id": 1,
        "ai_confidence": 0.95,
    },
    {
        "title": "Liverpool vs Arsenal: Anfield Awaits Crucial Premier League Clash",
        "content": "Liverpool prepare to host Arsenal at Anfield in what promises to be a crucial Premier League encounter. Both teams are fighting for European qualification spots, with Mohamed Salah and Bukayo Saka expected to be key players in this high-stakes match...",
        "summary": "Preview of Liverpool vs Arsenal at Anfield",
        "author": "AI Sports Writer",
        "status": "published",
        "tags": ["football", "Premier League", "Liverpool", "Arsenal", "Preview"],
        "game_id": 2,
        "ai_confidence": 0.88,
    },
]


class DatabaseSeeder:
    def __init__(self):
        """Initialize the database seeder with Supabase client."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_key:
            logger.error(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
            )
            sys.exit(1)

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Connected to Supabase")

    def clear_existing_data(self) -> None:
        """Clear existing seed data (for development)."""
        logger.info("Clearing existing seed data...")

        tables = ["articles", "games", "players", "teams"]
        for table in tables:
            try:
                _ = self.supabase.table(table).delete().neq("id", 0).execute()
                logger.info("Cleared %s table", table)
            except Exception as e:
                logger.warning("Could not clear %s: %s", table, e)

    def seed_teams(self) -> List[Dict]:
        """Seed teams data."""
        logger.info("Seeding teams...")

        result = self.supabase.table("teams").insert(SAMPLE_TEAMS).execute()
        teams = result.data
        logger.info("Created %d teams", len(teams))
        return teams

    def seed_players(self, teams: List[Dict]) -> List[Dict]:
        """Seed players data."""
        logger.info("Seeding players...")

        # Update team_ids with actual IDs from inserted teams
        players_data = []
        for player in SAMPLE_PLAYERS:
            player_copy = player.copy()
            # Map to actual team IDs
            team_index = player["team_id"] - 1
            if team_index < len(teams):
                player_copy["team_id"] = teams[team_index]["id"]
            players_data.append(player_copy)

        result = self.supabase.table("players").insert(players_data).execute()
        players = result.data
        logger.info("Created %d players", len(players))
        return players

    def seed_games(self, teams: List[Dict]) -> List[Dict]:
        """Seed games data."""
        logger.info("Seeding games...")

        # Update team_ids with actual IDs from inserted teams
        games_data = []
        for game in SAMPLE_GAMES:
            game_copy = game.copy()
            # Convert datetime to ISO string for JSON serialization
            if isinstance(game_copy["game_date"], datetime):
                game_copy["game_date"] = game_copy["game_date"].isoformat()

            # Map to actual team IDs
            home_index = game["home_team_id"] - 1
            away_index = game["away_team_id"] - 1

            if home_index < len(teams) and away_index < len(teams):
                game_copy["home_team_id"] = teams[home_index]["id"]
                game_copy["away_team_id"] = teams[away_index]["id"]

            games_data.append(game_copy)

        result = self.supabase.table("games").insert(games_data).execute()
        games = result.data
        logger.info("Created %d games", len(games))
        return games

    def seed_articles(self, games: List[Dict]) -> List[Dict]:
        """Seed articles data."""
        logger.info("Seeding articles...")

        # Update game_ids with actual IDs from inserted games
        articles_data = []
        for article in SAMPLE_ARTICLES:
            article_copy = article.copy()

            # Map to actual game ID
            game_index = article["game_id"] - 1
            if game_index < len(games):
                article_copy["game_id"] = games[game_index]["id"]

            # Convert tags list to JSON
            article_copy["tags"] = json.dumps(article_copy["tags"])

            articles_data.append(article_copy)

        result = self.supabase.table("articles").insert(articles_data).execute()
        articles = result.data
        logger.info("Created %d articles", len(articles))
        return articles

    def run(self, clear_first: bool = False) -> None:
        """Run the complete seeding process."""
        logger.info("🌱 Starting database seeding...")

        try:
            if clear_first:
                self.clear_existing_data()

            teams = self.seed_teams()
            players = self.seed_players(teams)
            games = self.seed_games(teams)
            articles = self.seed_articles(games)

            logger.info("✅ Database seeding complete!")
            logger.info(
                "Created: %d teams, %d players, %d games, %d articles",
                len(teams),
                len(players),
                len(games),
                len(articles),
            )

        except Exception as e:
            logger.error(f"❌ Seeding failed: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed Sport Scribe database")
    parser.add_argument(
        "--clear", action="store_true", help="Clear existing data first"
    )
    args = parser.parse_args()

    seeder = DatabaseSeeder()
    seeder.run(clear_first=args.clear)


if __name__ == "__main__":
    main()
