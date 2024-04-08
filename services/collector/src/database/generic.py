import abc
from contextlib import asynccontextmanager

import models


class Database(abc.ABC):
    @abc.abstractmethod
    async def add_competition_event(self, competition: models.Competition) -> int:
        pass

    @abc.abstractmethod
    async def add_competition_results(
            self,
            competition_id: int,
            results_mapping: dict[int, models.Result]
    ):
        pass

    @abc.abstractmethod
    async def add_runner(self, runner: models.Runner):
        pass

    @classmethod
    @asynccontextmanager
    async def session(cls):
        yield cls()
