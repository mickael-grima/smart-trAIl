import abc
from collections.abc import AsyncIterator

from collector import models


class ResultsScraper(abc.ABC):
    """Generic Results Scraper."""

    name: str

    @abc.abstractmethod
    async def scrap(self) -> AsyncIterator[models.Competition]:
        """
        Scrap whatever webpage is inheriting from Scraper.

        Returns
        -------
        AsyncIterator[models.Competition]
            Iterate all scraped competitions.
        """
        yield


class MetadataScraper(abc.ABC):
    """Generic Metadata Scraper."""

    name: str

    @abc.abstractmethod
    async def scrap(self) -> AsyncIterator[models.CompetitionMetaData]:
        """
        Scrap whatever webpage is inheriting from Scraper.

        Returns
        -------
        AsyncIterator[models.Competition]
            Iterate all scraped competitions metadata.
        """
        yield
