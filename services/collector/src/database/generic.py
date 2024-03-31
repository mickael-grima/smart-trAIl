import abc
from contextlib import asynccontextmanager

import models


class Database(abc.ABC):
    @abc.abstractmethod
    async def add_competitions(self, competition: models.Competition):
        pass

    @abc.abstractmethod
    async def add_competition_results(self, competition_id: int, results: list[models.Result]):
        pass

    @abc.abstractmethod
    async def add_runners(self, runners: list[models.Runner]):
        pass

    @classmethod
    @asynccontextmanager
    async def session(cls):
        yield cls()
