import datetime
import logging
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy import delete, select
from sqlalchemy.dialects.mysql import insert, Insert
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, create_async_engine, AsyncEngine, AsyncSession)

import models
from . import env
from . import orm
from ..generic import Database

logger = logging.getLogger(__name__)


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
                f"{orm.Competition.__tablename__}, {orm.Result.__tablename__}")
            await conn.run_sync(orm.Base.metadata.create_all)

    @classmethod
    @asynccontextmanager
    async def session(cls):
        self = await cls.create()
        try:
            yield self
        finally:
            await self.dispose()

    @asynccontextmanager
    async def __db_session(self) -> AsyncContextManager[AsyncSession]:
        async_session = async_sessionmaker(self._engine)
        async with async_session() as session:
            async with session.begin():
                yield session

    async def __insert(self, stmt: Insert) -> list[int]:
        """
        Execute insert statement
        :return: the sorted list of newly created ids, in the order
            of the provided data
        """
        async with self.__db_session() as session:
            result = await session.execute(stmt)
            return result.inserted_primary_key

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
        res = await self.__insert(stmt)
        comp_id = int(res[0])
        if comp_id > 0:
            return comp_id
        return await self.get_competition_id(
            competition.name,
            competition.timekeeper,
        )

    async def add_competition_event(
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
        res = await self.__insert(stmt)
        event_id = int(res[0])
        if event_id > 0:
            return event_id
        return await self.get_competition_event_id(
            competition.event,
            competition.date.start,
            competition.distance,
        )

    async def add_runner(self, runner: models.Runner) -> int | None:
        """
        add runners that are not yet stored in the db
        :return: the sorted list of newly created ids, in the order
            of the provided runners
        """
        obj = orm.Runner.from_model(runner)
        stmt = insert(orm.Runner).values(obj)
        stmt = stmt.on_duplicate_key_update(gender=stmt.inserted.gender)
        res = await self.__insert(stmt)
        runner_id = int(res[0])
        if runner_id > 0:
            return runner_id
        return await self.get_runner_id(
            runner.first_name,
            runner.last_name,
            runner.birth_year,
        )

    async def add_competition_results(
            self,
            event_id: int,
            results_mapping: dict[int, models.Result]
    ):
        """
        Careful: this step suppose that the corresponding competition and runners
        are already stored in the DB
        """
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

    async def get_runner_id(self, fname: str, lname: str, birth_year: int) -> int | None:
        """
        Get runner id from the DB
        """
        stmt = select(orm.Runner.id).where(
            orm.Runner.first_name == fname and
            orm.Runner.last_name == lname and
            orm.Runner.birth_year == birth_year
        )
        async with self.__db_session() as session:
            res = await session.execute(stmt)
            runner_id = res.fetchone()
            if runner_id is not None:
                return runner_id[0]

    async def get_competition_id(self, name: str, timekeeper: str) -> int | None:
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

    async def get_competition_event_id(
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
