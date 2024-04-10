import abc
from contextlib import asynccontextmanager

import models


class Database(abc.ABC):
    @abc.abstractmethod
    async def add_competition(self, competition: models.Competition):
        """
        Add everything around the given competition:
        - competition & event itself
        - all the runners involved
        - all the results
        """

    @classmethod
    @asynccontextmanager
    async def session(cls):
        yield cls()
