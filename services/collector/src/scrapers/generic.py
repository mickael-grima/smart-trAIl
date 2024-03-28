import abc
from typing import AsyncIterator

import models


class Scraper(abc.ABC):
    @abc.abstractmethod
    async def scrap(self) -> AsyncIterator[models.Competition]:
        pass
