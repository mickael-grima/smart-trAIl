import abc
from typing import AsyncIterator

import models


class Scraper(abc.ABC):
    name: str

    @abc.abstractmethod
    async def scrap(self) -> AsyncIterator[models.Competition]:
        """
        Scrap whatever webpage is inheriting from Scraper
        and yield the competitions
        """
