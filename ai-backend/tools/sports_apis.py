"""
Sports APIs Module

This module provides interface for API-Football from RapidAPI.
Focus: Football (Soccer) only for MVP.
"""

import logging
import os
from typing import Any

import aiohttp
from dotenv import load_dotenv

from utils.security import sanitize_log_input, sanitize_multiple_log_inputs

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIFootballClient:
    """
    Client for API-Football from RapidAPI integration.

    Documentation: https://rapidapi.com/api-sports/api/api-football
    Focus: Football (Soccer) data only for MVP
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"

        if self.api_key:
            self.headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
            }
        else:
            self.headers = {}

        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "APIFootballClient":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self.session:
            await self.session.close()

    async def get_fixtures(
        self,
        fixture_id: int | None = None,
        date: str | None = None,
        league: int | None = None,
        team: int | None = None,
        season: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get football fixtures/matches.

        Args:
            fixture_id: ID of the fixture (optional)
            date: Date in YYYY-MM-DD format (optional)
            league: League ID (optional)
            team: Team ID (optional)
            season: Season year (required if league is provided)

        Returns:
            List of fixture data dictionaries
        """

        if not self.headers or "X-RapidAPI-Key" not in self.headers:
            logger.error("Missing RapidAPI key in headers.")
            return []

        payload = self._build_fixture_payload(fixture_id, date, league, team, season)

        if not payload:
            logger.warning("get_fixtures called without any parameters.")
            return []

        url = self.base_url + "/fixtures"

        return await self._fetch_fixtures(url, payload)

    def _build_fixture_payload(
        self,
        fixture_id: int | None,
        date: str | None,
        league: int | None,
        team: int | None,
        season: int | None,
    ) -> dict[str, Any]:
        """Builds the payload for the fixture request."""
        payload = {}
        if fixture_id is not None:
            payload["id"] = sanitize_log_input(fixture_id)
        if date is not None:
            payload["date"] = sanitize_log_input(date)
        if league is not None:
            if season is None:
                logger.error("Season must be provided when filtering by league.")
                return {}  # Return empty dict to indicate failure
            payload["league"] = sanitize_log_input(league)
            payload["season"] = sanitize_log_input(season)
        if team is not None:
            payload["team"] = sanitize_log_input(team)
        return payload

    async def _fetch_fixtures(
        self, url: str, payload: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Fetches fixtures from the API."""
        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()

            async with self.session.get(
                url, headers=self.headers, params=payload
            ) as response:
                logger.info(
                    f"Requesting fixtures with params: {payload}. Status: {response.status}"
                )

                response.raise_for_status()

                data = await response.json()
                data_response = data.get("response", [])
                if not isinstance(data_response, list):
                    data_response = []
                return data_response

        except aiohttp.ClientError as e:
            logger.error(f"An error occurred while calling API-Football: {e}")
            return []

    async def get_teams(self, league_id: int, season: int) -> list[dict[str, Any]]:
        """
        Get teams in a league for a season.

        Args:
            league_id: League ID
            season: Season year

        Returns:
            List of team data dictionaries
        """
        # TODO: Implement API-Football teams endpoint
        league_safe, season_safe = sanitize_multiple_log_inputs(league_id, season)
        logger.info("Fetching teams for league %s, season %s", league_safe, season_safe)
        return []

    async def get_league_standings(self, league_id: int, season: int) -> dict[str, Any]:
        """
        Get league standings/table.

        Args:
            league_id: League ID
            season: Season year

        Returns:
            Dictionary containing league standings
        """
        # TODO: Implement API-Football standings endpoint
        league_safe, season_safe = sanitize_multiple_log_inputs(league_id, season)
        logger.info(
            "Fetching standings for league %s, season %s", league_safe, season_safe
        )
        return {}

    async def get_match_statistics(self, fixture_id: int) -> dict[str, Any]:
        """
        Get detailed match statistics.

        Args:
            fixture_id: Fixture/match ID

        Returns:
            Dictionary containing match statistics
        """
        # TODO: Implement API-Football match statistics endpoint
        logger.info(
            "Fetching match statistics for fixture %s", sanitize_log_input(fixture_id)
        )
        return {}

    async def get_players(self, team_id: int, season: int) -> list[dict[str, Any]]:
        """
        Get players from a team for a season.

        Args:
            team_id: Team ID
            season: Season year

        Returns:
            List of player data dictionaries
        """
        # TODO: Implement API-Football players endpoint
        team_safe, season_safe = sanitize_multiple_log_inputs(team_id, season)
        logger.info("Fetching players for team %s, season %s", team_safe, season_safe)
        return []


# Football League IDs for common leagues (API-Football)
FOOTBALL_LEAGUES = {
    "premier_league": 39,
    "la_liga": 140,
    "serie_a": 135,
    "bundesliga": 78,
    "ligue_1": 61,
    "champions_league": 2,
    "europa_league": 3,
    "world_cup": 1,
}
