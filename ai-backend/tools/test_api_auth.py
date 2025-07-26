import asyncio
import json
import logging
import os
from typing import Any

import aiohttp
from dotenv import load_dotenv

# from utils.security import sanitize_log_input, sanitize_multiple_log_inputs


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIAuth:
    """Authentication client for API-Football from RapidAPI."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"

        if self.api_key:
            self.headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
                "Content-Type": "application/json",
            }
        else:
            self.headers = {}

        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "APIAuth":
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
            self.session = None
            logger.info("API session closed.")
            return

        logger.error("API session not initialized.")
        return

    async def test_api_auth(self) -> list[dict[str, Any]]:

        if not self.headers or "x-rapidapi-key" not in self.headers:
            logger.error("Missing RapidAPI key in headers.")
            return []

        payload = {
            # "league": "39",
            # "season": "2023",
            "timezone": "Europe/London",
            "date": "2023-02-23",
        }

        url = self.base_url + "/fixtures"

        return await self._fetch_data(url, payload)

    async def _fetch_data(self, url, payload) -> list[dict[str, Any]]:
        try:
            async with self.session.get(
                url, headers=self.headers, params=payload
            ) as response:
                logger.info(f"Requesting data from {url}. Status: {response.status}")

                response.raise_for_status()

                data = await response.json()
                data_stringified = json.dumps(data, indent=2)

                # logger.info(f"Response data: {data_stringified}")
                return data_stringified

        except aiohttp.ClientError as e:
            logger.error(f"""An error occurred while calling API-Football: {e}""")
            return []


async def main():
    async with APIAuth() as api_auth:
        result = await api_auth.test_api_auth()
        print(f"API test result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
