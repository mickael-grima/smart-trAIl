import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from unittest.mock import Mock, patch

import pytest

from collector import main


@pytest.fixture()
def db():
    d = Mock()
    d.add_competition_calls = 0
    d.update_competition_calls = 0
    d.search_competitions_calls = 0

    async def add_competition(_):
        await asyncio.sleep(0.02)
        d.add_competition_calls += 1

    async def update_competition(*args):
        await asyncio.sleep(0.02)
        d.update_competition_calls += 1

    async def search_competitions():
        await asyncio.sleep(0.02)
        d.search_competitions_calls += 1
        return defaultdict(Mock)

    d.add_competition = add_competition
    d.update_competition = update_competition
    d.search_competitions = search_competitions

    @asynccontextmanager
    async def client():
        yield d

    with patch("collector.main.db_client", client):
        yield d


@pytest.fixture()
def scrapers():
    def mock_scraper():
        scraper = Mock()
        scraper.find_best_match = Mock(return_value=11)
        scraper.scrap_calls = 0

        async def scrap():
            yield Mock()
            scraper.scrap_calls += 1

        scraper.scrap = scrap

        return scraper

    scrapers = [mock_scraper(), mock_scraper()]

    with patch("collector.main.discover_timekeepers_scrapers", Mock(return_value=scrapers)), \
         patch("collector.main.discover_metadata_scrapers", Mock(return_value=scrapers)):
        yield scrapers


@pytest.mark.asyncio
async def test_run(db, scrapers):
    await main.run()

    assert db.add_competition_calls == 2
    assert db.update_competition_calls == 2
    assert db.search_competitions_calls == 2
    assert all([s.scrap_calls == 2 for s in scrapers])
