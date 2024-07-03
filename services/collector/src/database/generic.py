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

    @abc.abstractmethod
    async def update_competition(
            self,
            comp_id: int,
            competition: models.CompetitionMetaData
    ):
        """
        Find & Update the corresponding competition
        """

    @abc.abstractmethod
    async def search_competitions(self) -> dict[int, models.CompetitionMetaData]:
        """
        Get all competition events from the DB
        :return: a mapping (id -> event) for each found event
        """

    @classmethod
    @asynccontextmanager
    async def client(cls):
        yield cls()
