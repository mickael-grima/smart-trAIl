import asyncio
import datetime
import logging
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy import delete, select, update, ValuesBase
from sqlalchemy.dialects.mysql import insert, Insert
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, create_async_engine, AsyncEngine, AsyncSession)

import models
from . import env
from . import orm
from ..generic import Database

logger = logging.getLogger(__name__)

locks: dict[str, asyncio.Lock] = {}


def get_lock(name: str) -> asyncio.Lock:
    global locks
    lock = locks.get(name)
    if lock is None:
        lock = asyncio.Lock()
        locks[name] = lock
    return lock


class MySQLClient(Database):
    _engine: AsyncEngine

    @classmethod
    async def create(cls):
        self = cls()
        envs = env.Environments.parse()
        self._engine = create_async_engine(envs.url())
        await self.__create_tables()
        return self

    async def dispose(self):
        await self._engine.dispose()

    async def __create_tables(self):
        """
        Create all tables used by this database
        """
        async with self._engine.begin() as conn:
            logger.info(
                f"About to create (if not exist) tables {orm.Runner.__tablename__}, "
                f"{orm.Competition.__tablename__}, {orm.Result.__tablename__}, "
                f"{orm.CompetitionEvent.__tablename__}")
            await conn.run_sync(orm.Base.metadata.create_all)

    @classmethod
    @asynccontextmanager
    async def client(cls):
        self = await cls.create()
        try:
            yield self
        finally:
            await self.dispose()

    async def update_competition(
            self,
            comp_id: int,
            competition: models.CompetitionMetaData
    ):
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

    async def add_competition(self, competition: models.Competition):
        # first add competitions and runners, and collect their db ids
        runners = [result.runner for result in competition.results]
        ids = await asyncio.gather(
            self.__add_competition_event(competition),
            *[self.__add_runner(runner) for runner in runners]
        )

        # get competition id and runners ids
        event_id = ids[0]
        runner_ids = [rid for rid in ids[1:]]

        # map competition.id & runner.id to its result
        results: dict[int, models.Result] = {}
        for j, result in enumerate(competition.results):
            runner_id = runner_ids[j]
            if runner_id is None:
                logger.warning(f"Missing runner id for result={result}")
                continue
            results[runner_id] = result

        # store results
        if results:
            await self.__add_competition_results(event_id, results)

    @asynccontextmanager
    async def __db_session(self) -> AsyncContextManager[AsyncSession]:
        async_session = async_sessionmaker(self._engine)
        async with async_session() as session:
            async with session.begin():
                yield session

    async def __insert(self, stmt: Insert, lock_table: str) -> list[int]:
        """
        Execute insert statement

        :param stmt: INSERT stmt to execute
        :param lock_table: If not None, create an async lock unique to `lock_table` string
        (usually the table's name). Useful to avoid Deadlocks

        :return: the sorted list of newly created ids, in the order
            of the provided data
        """
        async with get_lock(lock_table):
            async with self.__db_session() as session:
                result = await session.execute(stmt)
                return result.inserted_primary_key

    async def __execute(self, stmt: ValuesBase, lock_table: str):
        """
        Execute insert statement

        :param stmt: DML stmt to execute
        :param lock_table: If not None, create an async lock unique to `lock_table` string
        (usually the table's name). Useful to avoid Deadlocks

        :return: the sorted list of newly created ids, in the order
            of the provided data
        """
        async with get_lock(lock_table):
            async with self.__db_session() as session:
                await session.execute(stmt)

    async def __add_competition(
            self,
            competition: models.Competition
    ) -> int | None:
        """
        Add competitions that are not yet stored in the DB
        :return: the sorted list of newly created ids, in the order
            of the provided competitions
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
    ) -> int | None:
        comp_id = await self.__add_competition(competition)
        if comp_id is None:
            return None

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

    async def __add_runner(self, runner: models.Runner) -> int | None:
        """
        add runners that are not yet stored in the db
        :return: the sorted list of newly created ids, in the order
            of the provided runners
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
    ):
        """
        Careful: this step suppose that the corresponding competition and runners
        are already stored in the DB
        """
        async with get_lock(orm.Result.__tablename__):
            async with self.__db_session() as session:
                # first remove results for this competition
                stmt = delete(orm.Result).where(orm.Result.event_id == event_id)
                await session.execute(stmt)

                # add results
                stmt = insert(orm.Result).values([
                    orm.Result.from_model(result, event_id, runner_id)
                    for runner_id, result in results_mapping.items()
                ])
                await session.execute(stmt)

    async def __get_runner_id(self, fname: str, lname: str, birth_year: int) -> int | None:
        """
        Get runner id from the DB
        """
        stmt = select(orm.Runner.id).where(
            orm.Runner.first_name == fname,
            orm.Runner.last_name == lname,
            orm.Runner.birth_year == birth_year
        )
        async with self.__db_session() as session:
            res = await session.execute(stmt)
            runner_id = res.fetchone()
            if runner_id is not None:
                return runner_id[0]

    async def __get_competition_id(self, name: str, timekeeper: str) -> int | None:
        """
        Get competition id from the DB
        """
        stmt = select(orm.Competition.id).where(
            orm.Competition.name == name and
            orm.Competition.timekeeper == timekeeper
        )
        async with self.__db_session() as session:
            res = await session.execute(stmt)
            comp_id = res.fetchone()
            if comp_id is not None:
                return comp_id[0]

    async def __get_competition_event_id(
            self,
            name: str,
            start_date: datetime.date,
            distance: float
    ) -> int | None:
        """
        Get competition id from the DB
        """
        stmt = select(orm.CompetitionEvent.id).where(
            orm.CompetitionEvent.name == name and
            orm.CompetitionEvent.distance == distance and
            orm.CompetitionEvent.start_date == start_date.strftime("%Y-%m-%d")
        )
        async with self.__db_session() as session:
            res = await session.execute(stmt)
            event_id = res.fetchone()
            if event_id is not None:
                return event_id[0]
