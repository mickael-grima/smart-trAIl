import os
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from urllib.parse import urlparse

import pytest

from ...context import scrapers, models
from scrapers.runraid import RunRaidScraper, utils

curr_dir = os.path.dirname(os.path.realpath(__file__))


def read_data_file(name: str) -> str:
    with open(Path(curr_dir, 'data', name)) as f:
        return f.read()


htmls: dict[str, str] = {
    "calendrier": read_data_file("calendrier.html.test"),
}


def mock_http_client():
    client = Mock()

    async def get(url: str):
        parsed = urlparse(url)
        match parsed.path:
            case "/calendrier.php":
                return htmls["calendrier"]
            case _:
                raise ValueError(f"url={url} not supported for testing")

    client.get = get
    return client


@patch("scrapers.runraid.main.client", mock_http_client())
@patch("scrapers.runraid.main.limiter.__aenter__", AsyncMock())
@patch("scrapers.runraid.main.limiter.__aexit__", AsyncMock())
@pytest.mark.asyncio
async def test_RunRaidScraper_scrap():
    scraper = RunRaidScraper()
    competitions = [c async for c in scraper.scrap()]
    assert len(competitions) == 258

    # check if some competitions are in
    expected = [
        models.CompetitionMetaData(
            event="Mare Longue Trail",
            distance=12,
            date=models.Date(start=utils.parse_date("20-01-2024")),
        ),
        models.CompetitionMetaData(
            event="Trans Volcano",
            distance=40,
            positive_elevation=2550,
            negative_elevation=2550,
            date=models.Date(start=utils.parse_date("04-02-2024")),
        ),
        models.CompetitionMetaData(
            event="Trans Volcano",
            distance=66,
            positive_elevation=2550,
            negative_elevation=2550,
            date=models.Date(start=utils.parse_date("04-02-2024")),
        ),
        models.CompetitionMetaData(
            event="Trail des Cordistes",
            distance=22,
            positive_elevation=1100,
            date=models.Date(start=utils.parse_date("07-04-2024")),
        ),
        models.CompetitionMetaData(
            event="D-Tour 45 et 70 km",
            distance=45,
            date=models.Date(start=utils.parse_date("20-04-2024")),
        ),
        models.CompetitionMetaData(
            event="D-Tour 45 et 70 km",
            distance=70,
            positive_elevation=3000,
            date=models.Date(start=utils.parse_date("20-04-2024")),
        ),
    ]
    for exp in expected:
        found = False
        for comp in competitions:
            if (
                comp.event == exp.event and
                comp.distance == exp.distance and
                comp.positive_elevation == exp.positive_elevation and
                comp.negative_elevation == exp.negative_elevation and
                comp.date == exp.date
            ):
                found = True
                break
        assert found, f"No competition={exp} found when it was expected"
