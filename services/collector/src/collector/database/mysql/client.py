import asyncio
import datetime
import logging
from contextlib import AbstractAsyncContextManager
from contextlib import asynccontextmanager

from sqlalchemy import delete, select, update, ValuesBase
from sqlalchemy.dialects.mysql import insert, Insert
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, create_async_engine, AsyncEngine, AsyncSession)

from collector import models
from collector.database.generic import Database
from collector.database.mysql import env
from collector.database.mysql import orm

logger = logging.getLogger(__name__)

locks: dict[str, asyncio.Lock] = {}


def get_lock(name: str) -> asyncio.Lock:
    """Create & Get an asyncio lock."""
    lock = locks.get(name)
    if lock is None:
        lock = asyncio.Lock()
        locks[name] = lock
    return lock


class MySQLClient(Database):
    """MySQL Database Client."""

    _engine: AsyncEngine

    @classmethod
    async def create(cls) -> "MySQLClient":
        """Create a client object, asynchronously."""
        self = cls()
        envs = env.Environments.parse()
        self._engine = create_async_engine(envs.url())
        await self.__create_tables()
        return self

    async def dispose(self) -> None:
        """Dispose the client object."""
        await self._engine.dispose()

    async def __create_tables(self) -> None:
        """Create all tables used by this database."""
        async with self._engine.begin() as conn:
            logger.info(
                "About to create (if not exist) tables %s, %s, %s, %s",
                orm.Runner.__tablename__, orm.Competition.__tablename__,
                orm.Result.__tablename__, orm.CompetitionEvent.__tablename__)
            await conn.run_sync(orm.Base.metadata.create_all)

    @classmethod
    @asynccontextmanager
    async def client(cls) -> AbstractAsyncContextManager["MySQLClient"]:
        """Yield the database client after creating it."""
        self = await cls.create()
        try:
            yield self
        finally:
            await self.dispose()

    async def search_competitions(self) -> dict[int, models.CompetitionMetaData]:
        """
        Get all competition events from the database.

        Returns
        -------
        dict[int, models.CompetitionMetaData]
            a mapping (id -> event) for each found competition.
        """
        async with self.__db_session() as session:
            res = await session.execute(select(orm.CompetitionEvent))
            rows = res.scalars().all()
            return {
                row.id: row.to_competition_metadata()
                for row in rows
            }

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
        stmt = (
            update(orm.CompetitionEvent)
            .where(orm.CompetitionEvent.id ==  comp_id)
            .values(
                distance=competition.distance,
                positive_elevation=competition.positive_elevation,
                negative_elevation=competition.negative_elevation,
            )
        )
        await self.__execute(stmt, orm.CompetitionEvent.__tablename__)

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
        # first add competitions and runners, and collect their db ids
        runners = [result.runner for result in competition.results]
        ids = await asyncio.gather(
            self.__add_competition_event(competition),
            *[self.__add_runner(runner) for runner in runners]
        )

        # get competition id and runners ids
        event_id, runner_ids = ids[0], ids[1:]

        # map competition.id & runner.id to its result
        results: dict[int, models.Result] = {}
        for j, result in enumerate(competition.results):
            runner_id = runner_ids[j]
            if runner_id is None:
                logger.warning("Missing runner id for result=%s", result)
                continue
            results[runner_id] = result

        # store results
        if results:
            await self.__add_competition_results(event_id, results)

    @asynccontextmanager
    async def __db_session(self) -> AbstractAsyncContextManager[AsyncSession]:
        async_session = async_sessionmaker(self._engine)
        async with async_session() as session, session.begin():
            yield session

    async def __insert(self, stmt: Insert, lock_table: str) -> list[int]:
        """
        Execute insert statement.

        Parameters
        ----------
        stmt: Insert
            INSERT stmt to execute.
        lock_table: str
            If not None, create an async lock unique to `lock_table` string
            (usually the table's name). Useful to avoid Deadlocks.

        Returns
        -------
        list[int]
            the sorted list of newly created ids, in the order
            of the provided data.
        """
        async with get_lock(lock_table), self.__db_session() as session:
            result = await session.execute(stmt)
            return result.inserted_primary_key

    async def __execute(self, stmt: ValuesBase, lock_table: str) -> None:
        """
        Execute insert statement.

        Parameters
        ----------
        stmt: ValuesBase
            DML stmt to execute.
        lock_table: str
            If not None, create an async lock unique to `lock_table` string
            (usually the table's name). Useful to avoid Deadlocks.
        """
        async with get_lock(lock_table), self.__db_session() as session:
            await session.execute(stmt)

    async def __add_competition(
            self,
            competition: models.Competition
    ) -> int:
        """
        Add competitions that are not yet stored in the DB.

        Parameters
        ----------
        competition: models.Competition
            The competition to add in the database.

        Returns
        -------
        int
            The competition unique id.
        """
        obj = orm.Competition.from_model(competition)
        stmt = insert(orm.Competition).values(obj)
        stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name
        )
        res = await self.__insert(stmt, orm.Competition.__tablename__)
        comp_id = int(res[0])
        if comp_id > 0:
            return comp_id
        return await self.__get_competition_id(
            competition.name,
            competition.timekeeper,
        )

    async def __add_competition_event(
            self,
            competition: models.Competition
    ) -> int:
        """
        Add competition event and underlying competition.

        Parameters
        ----------
        competition: models.Competition
            The competition to add in the database.

        Returns
        -------
        int
            The unique competition event id.
        """
        comp_id = await self.__add_competition(competition)
        obj = orm.CompetitionEvent.from_model(comp_id, competition)
        stmt = insert(orm.CompetitionEvent).values(obj)
        stmt = stmt.on_duplicate_key_update(
            distance=stmt.inserted.distance
        )
        res = await self.__insert(stmt, orm.CompetitionEvent.__tablename__)
        event_id = int(res[0])
        if event_id > 0:
            return event_id
        return await self.__get_competition_event_id(
            competition.event,
            competition.date.start,
            competition.distance,
        )

    async def __add_runner(self, runner: models.Runner) -> int:
        """
        Add runners that are not yet stored in the database.

        Parameters
        ----------
        runner: models.Runner
            The runner to add in the database.

        Returns
        -------
        int
            The added runner's unique id.
        """
        obj = orm.Runner.from_model(runner)
        stmt = insert(orm.Runner).values(obj)
        stmt = stmt.on_duplicate_key_update(gender=stmt.inserted.gender)
        res = await self.__insert(stmt, orm.Runner.__tablename__)
        runner_id = int(res[0])
        if runner_id > 0:
            return runner_id
        return await self.__get_runner_id(
            runner.first_name,
            runner.last_name,
            runner.birth_year,
        )

    async def __add_competition_results(
            self,
            event_id: int,
            results_mapping: dict[int, models.Result]
    ) -> None:
        """
        Add runners results in the database.

        Careful: this step suppose that the corresponding competition and
        runners are already stored in the DB.

        Parameters
        ----------
        event_id: int
            The competition event id.
        results_mapping: dict[int, models.Result]
            The mapping runner's id -> result to be added in the DB.
        """
        async with get_lock(orm.Result.__tablename__), \
                self.__db_session() as session:
            # first remove results for this competition
            stmt = delete(orm.Result).where(orm.Result.event_id == event_id)
            await session.execute(stmt)

            # add results
            stmt = insert(orm.Result).values([
                orm.Result.from_model(result, event_id, runner_id)
                for runner_id, result in results_mapping.items()
            ])
            await session.execute(stmt)

    async def __get_runner_id(
            self, first_name: str, last_name: str, birth_year: int) -> int | None:
        """
        Get runner id from the Database.

        Parameters
        ----------
        first_name: str
            The runner first name.
        last_name: str
            The runner last name.
        birth_year: int
            The runner birth year.

        Returns
        -------
        Optional[int]
            The runner's unique id, if any found.
        """
        stmt = select(orm.Runner.id).where(
            orm.Runner.first_name == first_name,
            orm.Runner.last_name == last_name,
            orm.Runner.birth_year == birth_year
        )
        async with self.__db_session() as session:
            res = await session.execute(stmt)
            runner_id = res.fetchone()
            return runner_id[0] if runner_id is not None else None

    async def __get_competition_id(
            self, name: str, timekeeper: str) -> int | None:
        """
        Get competition id from the database.

        Parameters
        ----------
        name: str
            The competition's name.
        timekeeper: str
            The competition's timekeeper.

        Returns
        -------
        int
            The competition unique id, if any found.
        """
        stmt = select(orm.Competition.id).where(
            orm.Competition.name == name and
            orm.Competition.timekeeper == timekeeper
        )
        async with self.__db_session() as session:
            res = await session.execute(stmt)
            comp_id = res.fetchone()
            return comp_id[0] if comp_id is not None else None

    async def __get_competition_event_id(
            self,
            name: str,
            start_date: datetime.date,
            distance: float
    ) -> int | None:
        """
        Get competition event id from the database.

        Parameters
        ----------
        name: str
            The competition event's name.
        start_date: datetime.date
            The competition event's start date.
        distance: float
            The competition distance.

        Returns
        -------
        Optional[int]
            The competition event unique id, if any found.
        """
        stmt = select(orm.CompetitionEvent.id).where(
            orm.CompetitionEvent.name == name and
            orm.CompetitionEvent.distance == distance and
            orm.CompetitionEvent.start_date == start_date.strftime("%Y-%m-%d")
        )
        async with self.__db_session() as session:
            res = await session.execute(stmt)
            event_id = res.fetchone()
            return event_id[0] if event_id is not None else None
