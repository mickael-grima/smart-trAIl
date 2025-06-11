from collections.abc import Iterable

from collector.scrapers.generic import ResultsScraper, MetadataScraper
from collector.scrapers.runraid import RunRaidScraper
from collector.scrapers.sportpro import SportproScraper

timekeepers_scrapers: dict[str, ResultsScraper] = {
    'sportpro': SportproScraper(),
}

metadata_scrapers: dict[str, MetadataScraper] = {
    'runraid': RunRaidScraper(),
}


def discover_timekeepers(
        scrapers: list[str] | None = None) -> Iterable[ResultsScraper]:
    """
    Discover timekeepers scrappers.

    Parameters
    ----------
    scrapers : list[str] | None
        The list of scrapers to return. If None, return all of them.

    Returns
    -------
    Iterable[ResultsScraper]
        Iterate all the timekeeper scrapers if `scrapers` is None,
        or the ones corresponding to scrapers names.
    """
    if scrapers is None:
        return timekeepers_scrapers.values()
    return [timekeepers_scrapers[s] for s in scrapers]


def discover_metadata_scrapers(
        scrapers: list[str] | None = None) -> Iterable[MetadataScraper]:
    """
    Discover metadata scrappers.

    Parameters
    ----------
    scrapers : list[str] | None
        The list of scrapers to return. If None, return all of them.

    Returns
    -------
    Iterable[ResultsScraper]
        Iterate all the metadata scrapers if `scrapers` is None,
        or the ones corresponding to scrapers names.
    """
    if scrapers is None:
        return metadata_scrapers.values()
    return [metadata_scrapers[s] for s in scrapers]
