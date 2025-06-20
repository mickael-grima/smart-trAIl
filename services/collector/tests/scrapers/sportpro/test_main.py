import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from urllib.parse import urlparse

import pytest

from collector.scrapers.sportpro import SportproScraper

curr_dir = os.path.dirname(os.path.realpath(__file__))


def read_data_file(name: str) -> str:
    with open(Path(curr_dir, 'data', name)) as f:
        return f.read()


htmls: dict[str, str] = {
    "resultats": read_data_file("resultats.html.test"),
    "transvolcano": read_data_file("transvolcano-longue.html.test"),
    "tangue": read_data_file("tangue.html.test"),
}


@pytest.fixture
def mock_http_client():
    client = Mock()

    async def get(url: str):
        parsed = urlparse(url)
        match parsed.path:
            case "/resultats/":
                return htmls["resultats"]
            case "/resultats/epreuve/05077-transvolcano-version-longue/":
                return htmls["transvolcano"]
            case "/resultats/epreuve/05079-tangue/":
                return htmls["tangue"]
            case _:
                raise ValueError(f"url={url} not supported for testing")

    client.get = get
    return client


class TestSportproScraper:
    @patch("collector.scrapers.sportpro.main.limiter.__aenter__", AsyncMock())
    @patch("collector.scrapers.sportpro.main.limiter.__aexit__", AsyncMock())
    @pytest.mark.asyncio
    async def test_scrap(self, mock_http_client):
        scraper = SportproScraper()
        with patch("collector.scrapers.sportpro.main.client", mock_http_client):
            competitions = list([c async for c in scraper.scrap()])
        assert len(competitions) == 2, f"errors={scraper._errors}"
        assert len(scraper._errors) == 2

        # check transvolcano results
        transvolcano = [c for c in competitions if c.event == "Transvolcano Version Longue"][0]
        assert len(transvolcano.results) == 336

        # check tangue results
        tangue = [c for c in competitions if c.event == "Tangue"][0]
        assert len(tangue.results) == 544 + 192
        assert len([r for r in tangue.results if r.rank is not None]) == 544
        assert len([r for r in tangue.results if r.rank is None]) == 192
