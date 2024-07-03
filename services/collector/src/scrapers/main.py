from .generic import ResultsScraper, MetadataScraper
from .sportpro import SportproScraper
from .runraid import RunRaidScraper


def discover_timekeepers() -> list[ResultsScraper]:
    return [SportproScraper()]


def discover_metadata_scrapers() -> list[MetadataScraper]:
    return [RunRaidScraper()]
