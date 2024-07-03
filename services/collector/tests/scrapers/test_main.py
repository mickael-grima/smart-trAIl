from ..context import scrapers
from scrapers.sportpro import SportproScraper
from scrapers.runraid import RunRaidScraper


def test_discover_metadata_scrapers():
    res = scrapers.discover_metadata_scrapers()
    assert len(res) == 1
    assert isinstance(res[0], RunRaidScraper)


def test_discover_timekeepers():
    res = scrapers.discover_timekeepers()
    assert len(res) == 1
    assert isinstance(res[0], SportproScraper)
