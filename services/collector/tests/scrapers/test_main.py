from ..context import scrapers
from scrapers.sportpro import SportproScraper


def test_discover():
    res = scrapers.discover()
    assert len(res) == 1
    assert isinstance(res[0], SportproScraper)
