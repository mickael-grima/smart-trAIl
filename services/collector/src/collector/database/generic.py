import abc
from contextlib import asynccontextmanager, AbstractAsyncContextManager

from collector import models


class Database(abc.ABC):
    """Database interface."""

    @abc.abstractmethod
    async def add_competition(self, competition: models.Competition) -> None:
        """
        Add a competition to the database.

        Add everything around the given competition:
        - competition & event itself
        - all the runners involved
        - all the results

        Parameters
        ----------
        competition: models.Competition
            The competition to add.
        """

    @abc.abstractmethod
    async def update_competition(
            self,
            comp_id: int,
            competition: models.CompetitionMetaData
    ) -> None:
        """
        Find & Update the corresponding competition.

        Parameters
        ----------
        comp_id: int
            The competition unique id.
        competition: models.CompetitionMetaData
            The competition data to update.
        """

    @abc.abstractmethod
    async def search_competitions(self) -> dict[int, models.CompetitionMetaData]:
        """
        Get all competition events from the database.

        Returns
        -------
        dict[int, models.CompetitionMetaData]
            a mapping (id -> event) for each found competition.
        """

    @classmethod
    @asynccontextmanager
    async def client(cls) -> AbstractAsyncContextManager["Database"]:
        """Yield the database client."""
        yield cls()
