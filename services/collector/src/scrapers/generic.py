import abc
from typing import AsyncIterator

import models


class ResultsScraper(abc.ABC):
    name: str

    @abc.abstractmethod
    async def scrap(self) -> AsyncIterator[models.Competition]:
        """
        Scrap whatever webpage is inheriting from Scraper
        and yield the competitions
        """
        yield


class MetadataScraper(abc.ABC):
    name: str

    @abc.abstractmethod
    async def scrap(self) -> AsyncIterator[models.CompetitionMetaData]:
        """
        Scrap whatever webpage is inheriting from Scraper
        and yield the competitions metadata
        """
        yield
