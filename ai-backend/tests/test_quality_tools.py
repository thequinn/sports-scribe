"""Sample code to test quality tools."""

import asyncio


class FootballDataProcessor:
    """Process football data for AI analysis."""

    def __init__(self, league: str) -> None:
        """Initialize processor with league."""
        self.league = league
        self.processed_games: list[dict[str, str]] = []

    def process_game_data(
        self, home_team: str, away_team: str, score: str | None = None
    ) -> dict[str, str]:
        """Process individual game data.

        Args:
            home_team: Name of home team
            away_team: Name of away team
            score: Optional match score

        Returns:
            Processed game data dictionary
        """
        game_data = {
            "home_team": home_team.strip(),
            "away_team": away_team.strip(),
            "league": self.league,
        }

        if score:
            game_data["score"] = score.strip()

        return game_data

    async def fetch_recent_games(self, limit: int = 10) -> list[dict[str, str]]:
        """Fetch recent games asynchronously.

        Args:
            limit: Maximum number of games to fetch

        Returns:
            list of recent games
        """
        # Simulate async API call
        await asyncio.sleep(0.1)

        return [
            self.process_game_data("Arsenal", "Chelsea", "2-1"),
            self.process_game_data("Liverpool", "Manchester City", "1-3"),
        ][:limit]


def main() -> None:
    """Main function to test the processor."""
    processor = FootballDataProcessor("Premier League")

    # Test synchronous processing
    game = processor.process_game_data("Arsenal", "Chelsea", "2-1")
    print(f"Processed game: {game}")


if __name__ == "__main__":
    main()
