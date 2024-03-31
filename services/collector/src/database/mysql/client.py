from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy import delete, insert

import models
from . import env
from . import orm
from ..generic import Database


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
    async def __session(self) -> AsyncContextManager[AsyncSession]:
        async_session = async_sessionmaker(self._engine)
        async with async_session() as session:
            async with session.begin():
                yield session

    async def add_competitions(self, competitions: list[models.Competition]):
        """
        Add competitions that are not yet stored in the DB
        """
        async with self.__session() as session:
            stmt = insert(orm.Competition).values([
                orm.Competition.from_model(competition)
                for competition in competitions
            ])
            stmt = stmt.on_duplicate_key_update(data=stmt.inserted.data)
            await session.execute(stmt)

    async def add_competition_results(self, competition_id: int, results: list[models.Result]):
        """
        Careful: this step suppose that the corresponding competition and runners
        are already stored in the DB
        """
        async with self.__session() as session:
            # first remove results for this competition
            stmt = delete(orm.Result).where(orm.Result.competition_id == competition_id)
            await session.execute(stmt)

            # add results
            await session.add_all([
                orm.Result.from_model(
                    result,
                    competition_id,
                    result.runner.id,
                )
                for result in results
            ])

    async def add_runners(self, runners: list[models.Runner]):
        async with self.__session() as session:
            stmt = insert(orm.Runner).values([
                orm.Runner.from_model(runner)
                for runner in runners
            ])
            stmt = stmt.on_duplicate_key_update(data=stmt.inserted.data)
            await session.execute(stmt)
