import asyncio
from contextlib import asynccontextmanager
from unittest.mock import Mock, AsyncMock, patch

import pytest

from .context import main


@pytest.fixture()
def db():
    d = Mock()
    d.add_competition_calls = 0

    async def add_competition(_):
        await asyncio.sleep(0.02)
        d.add_competition_calls += 1

    d.add_competition = add_competition

    @asynccontextmanager
    async def client():
        yield d

    with patch("main.db_client", client):
        yield d


@pytest.fixture()
def scrapers():
    def mock_scraper():
        scraper = Mock()
        scraper.scrap_calls = 0

        async def scrap():
            yield "test"
            scraper.scrap_calls += 1

        scraper.scrap = scrap

        return scraper

    scrapers = [mock_scraper(), mock_scraper()]

    with patch("main.discover_scrapers", Mock(return_value=scrapers)):
        yield scrapers


@pytest.mark.asyncio
async def test_run(db, scrapers):
    await main.run()

    assert db.add_competition_calls == 2
    assert all([s.scrap_calls == 1 for s in scrapers])
