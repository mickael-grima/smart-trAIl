from typing import Iterable

from .generic import ResultsScraper, MetadataScraper
from .sportpro import SportproScraper
from .runraid import RunRaidScraper

timekeepers_scrapers: dict[str, ResultsScraper] = {
    'sportpro': SportproScraper(),
}

metadata_scrapers: dict[str, MetadataScraper] = {
    'runraid': RunRaidScraper(),
}


def discover_timekeepers(scrapers: list[str] = None) -> Iterable[ResultsScraper]:
    """
    return all the timekeeper scrapers if `scrapers` is None,
    or the ones corresponding to scrapers
    """
    if scrapers is None:
        return timekeepers_scrapers.values()
    return [timekeepers_scrapers[s] for s in scrapers]


def discover_metadata_scrapers(scrapers: list[str] = None) -> Iterable[MetadataScraper]:

    """
    return all the timekeeper scrapers if `scrapers` is None,
    or the ones corresponding to scrapers
    """
    if scrapers is None:
        return metadata_scrapers.values()
    return [metadata_scrapers[s] for s in scrapers]
