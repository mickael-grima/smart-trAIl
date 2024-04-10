from .generic import Scraper
from .sportpro import SportproScraper


def discover() -> list[Scraper]:
    return [SportproScraper()]
