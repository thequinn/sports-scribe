import pytest

from tools.sports_apis import APIFootballClient


@pytest.mark.asyncio
async def test_get_fixtures_by_league(monkeypatch):
    class MockResponse:
        status = 200

        async def json(self):
            return {"response": [{"fixture": 1, "league": 39, "season": 2025}]}

        def raise_for_status(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponse()

    client = APIFootballClient(api_key="test")
    client.session = MockSession()
    result = await client.get_fixtures(league=39, season=2025)
    assert isinstance(result, list)
    assert result[0]["league"] == 39
    assert result[0]["season"] == 2025


@pytest.mark.asyncio
async def test_get_fixtures_by_league_missing_season(monkeypatch):
    client = APIFootballClient(api_key="test")
    result = await client.get_fixtures(league=39)
    assert result == []


@pytest.mark.asyncio
async def test_get_fixtures_by_date(monkeypatch):
    class MockResponse:
        status = 200

        async def json(self):
            return {"response": [{"fixture": 2, "date": "2025-07-10"}]}

        def raise_for_status(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponse()

    client = APIFootballClient(api_key="test")
    client.session = MockSession()
    result = await client.get_fixtures(date="2025-07-10")
    assert isinstance(result, list)
    assert result[0]["date"] == "2025-07-10"


@pytest.mark.asyncio
async def test_get_fixtures_by_team(monkeypatch):
    class MockResponse:
        status = 200

        async def json(self):
            return {"response": [{"fixture": 3, "team": 100}]}

        def raise_for_status(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponse()

    client = APIFootballClient(api_key="test")
    client.session = MockSession()
    result = await client.get_fixtures(team=100)
    assert isinstance(result, list)
    assert result[0]["team"] == 100


@pytest.mark.asyncio
async def test_get_fixtures_by_multiple(monkeypatch):
    class MockResponse:
        status = 200

        async def json(self):
            return {
                "response": [
                    {
                        "fixture": 4,
                        "league": 39,
                        "season": 2025,
                        "date": "2025-07-10",
                        "team": 100,
                    }
                ]
            }

        def raise_for_status(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponse()

    client = APIFootballClient(api_key="test")
    client.session = MockSession()
    result = await client.get_fixtures(league=39, season=2025, date="2025-07-10", team=100)
    assert isinstance(result, list)
    assert result[0]["league"] == 39
    assert result[0]["date"] == "2025-07-10"
    assert result[0]["team"] == 100


@pytest.mark.asyncio
async def test_get_fixtures_no_params(monkeypatch):
    client = APIFootballClient(api_key="test")
    result = await client.get_fixtures()
    assert result == []
