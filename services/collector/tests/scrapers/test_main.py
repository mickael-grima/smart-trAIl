import pytest

from ..context import scrapers
from scrapers import MetadataScraper, ResultsScraper
from scrapers.sportpro import SportproScraper
from scrapers.runraid import RunRaidScraper


def is_equal(
        res: list[MetadataScraper | ResultsScraper],
        expected: list[MetadataScraper | ResultsScraper]
):
    assert len(res) == len(expected)
    for i in range(len(res)):
        assert isinstance(res[i], expected[i].__class__)


@pytest.mark.parametrize(
    "scrapers_,expected",
    [
        (None, [RunRaidScraper()]),
        (['runraid'], [RunRaidScraper()]),
    ]
)
def test_discover_metadata_scrapers(
        scrapers_: list[str] | None,
        expected: list[MetadataScraper] | Exception):
    res = list(scrapers.discover_metadata_scrapers(scrapers=scrapers_))
    is_equal(res, expected)


def test_discover_metadata_scrapers_error():
    with pytest.raises(KeyError):
        scrapers.discover_metadata_scrapers(scrapers=["unknown"])


@pytest.mark.parametrize(
    "scrapers_,expected",
    [
        (None, [SportproScraper()]),
        (['sportpro'], [SportproScraper()]),
    ]
)
def test_discover_timekeepers(
        scrapers_: list[str] | None,
        expected: list[ResultsScraper] | Exception):
    res = list(scrapers.discover_timekeepers(scrapers=scrapers_))
    is_equal(res, expected)


def test_discover_timekeepers_scrapers_error():
    with pytest.raises(KeyError):
        scrapers.discover_timekeepers(scrapers=["unknown"])
