import os
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from urllib.parse import urlparse

import pytest

from ...context import scrapers

curr_dir = os.path.dirname(os.path.realpath(__file__))


def read_data_file(name: str) -> str:
    with open(Path(curr_dir, 'data', name)) as f:
        return f.read()


htmls: dict[str, str] = {
    "resultats": read_data_file("resultats.html.test"),
    "transvolcano": read_data_file("transvolcano-longue.html.test"),
}


def mock_http_client():
    client = Mock()

    async def get(url: str):
        parsed = urlparse(url)
        match parsed.path:
            case "/resultats/":
                return htmls["resultats"]
            case "/resultats/epreuve/05077-transvolcano-version-longue/":
                return htmls["transvolcano"]
            case _:
                raise ValueError(f"url={url} not supported for testing")

    client.get = get
    return client


@patch("scrapers.sportpro.main.client", mock_http_client())
@patch("scrapers.sportpro.main.limiter.__aenter__", AsyncMock())
@patch("scrapers.sportpro.main.limiter.__aexit__", AsyncMock())
@pytest.mark.asyncio
async def test_SportproScraper_scrap():
    scraper = scrapers.SportproScraper()
    competitions = list([c async for c in scraper.scrap()])
    assert len(competitions) == 1, f"errors={scraper._errors}"
    assert len(scraper._errors) == 3
