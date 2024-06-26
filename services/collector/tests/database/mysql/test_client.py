from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import AsyncContextManager
from unittest.mock import patch, Mock, AsyncMock

import pytest
from sqlalchemy import Select, Delete
from sqlalchemy.dialects.mysql import Insert

from ...context import database, models
from database.mysql import Client as MySQLClient, orm

competition = models.Competition(
    name="Transvolcano",
    event="Tangue",
    timekeeper="sportpro",
    date=models.Date(start=date(year=2024, month=1, day=22)),
    distance=23,
    results=[
        models.Result(
            runner=models.Runner(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=1992,
                gender=models.Gender.male,
            ),
            time=timedelta(hours=30, minutes=34, seconds=35),
            rank=models.Rank(
                scratch=23,
                gender=22,
                category=13,
            ),
            status=models.ResultStatus.finisher,
            race_number=34234,
            license="LICENCE",
            category="SEH"
        ),
        models.Result(
            runner=models.Runner(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=1992,
                gender=models.Gender.male,
            ),
            time=None,
            rank=None,
            status=models.ResultStatus.abandoned,
            race_number=34234,
            license="LICENCE",
            category="SEH"
        ),
    ],
)


@patch("database.mysql.env.Environments.url", Mock(return_value="mysql+asyncmy://root:xxx@test:3901/test"))
@pytest.fixture()
def mock_engine():
    """
    Mock MySQL engine
    """
    # mock engine
    engine = Mock()
    engine.dispose = AsyncMock()
    # store all connections
    engine.connections = []

    @asynccontextmanager
    async def begin() -> AsyncContextManager[Mock]:
        conn = Mock()
        conn.run_sync = AsyncMock()
        engine.connections.append(conn)
        yield conn

    engine.begin = begin

    with patch("database.mysql.client.create_async_engine", Mock(return_value=engine)):
        yield engine


@pytest.fixture()
def mock_session():
    """
    Mock async_sessionmaker
    """
    session = Mock()

    # used to fake a primary auto-incremented key
    # common to all tables for simplicity
    session.current_index = 0

    # list of executed statements
    session.statements = []

    async def execute(stmt):
        """
        Save the statement
        To force the program to get the id with a SELECT statement,
        make sure 0 is returned whenever it is an INSERT statement, to simulate
        a ON KEY UPDATE

        After 10 received statements, INSERT will return a non-zero id, to simulate
        a rela INSERT
        """
        nonlocal session
        session.statements.append(stmt)
        res = Mock()
        if isinstance(stmt, Insert):
            res.inserted_primary_key = [max(0, len(session.statements) - 10)]
        else:
            session.current_index += 1
            res.fetchone = Mock(return_value=[session.current_index])
        return res

    session.execute = execute

    @asynccontextmanager
    async def begin() -> AsyncContextManager[Mock]:
        yield

    session.begin = begin

    @asynccontextmanager
    async def async_session() -> AsyncContextManager[Mock]:
        yield session

    with patch("database.mysql.client.async_sessionmaker", Mock(return_value=async_session)):
        yield session


@pytest.mark.asyncio
async def test_MySQLClient_add_competition(mock_engine, mock_session):
    # ---------- first run, with existing data in DB (as if) ----------
    async with MySQLClient.client() as db:
        await db.add_competition(competition)

    # check table creations
    assert len(mock_engine.connections) == 1
    conn = mock_engine.connections[-1]
    conn.run_sync.assert_called_once_with(orm.Base.metadata.create_all)

    # check insertions & selects
    assert len(mock_session.statements) == 10
    # 1 time over 2, we try to insert, but the data are already in
    assert all([isinstance(s, Insert) for s in mock_session.statements[:8:2]])
    # 1 time over 2, we get the id with a SELECT
    assert all([isinstance(s, Select) for s in mock_session.statements[1:8:2]])
    # delete results
    assert isinstance(mock_session.statements[-2], Delete)
    # insert results
    assert isinstance(mock_session.statements[-1], Insert)

    # ---------- second run, with no data in DB ----------
    async with MySQLClient.client() as db:
        await db.add_competition(competition)

    # check table creations
    assert len(mock_engine.connections[1:]) == 1
    conn = mock_engine.connections[-1]
    conn.run_sync.assert_called_once_with(orm.Base.metadata.create_all)

    # check insertions & selects
    statements = mock_session.statements[10:]
    assert len(statements) == 6
    # all first statements are
    assert all([isinstance(s, Insert) for s in statements[:4]])
    # delete results
    assert isinstance(statements[-2], Delete)
    # insert results
    assert isinstance(statements[-1], Insert)


@pytest.mark.asyncio
async def test_MySQLClient_update_competition(mock_engine, mock_session):
    metadata = models.CompetitionMetaData(
        event="whatever",
        date=models.Date(start=date(year=2024, month=4, day=8)),
        distance=24.,
        positive_elevation=1050,
        negative_elevation=None,
    )

    async with MySQLClient.client() as db:
        await db.update_competition(1, metadata)

    # check table creations
    assert len(mock_engine.connections) == 1
    conn = mock_engine.connections[-1]
    conn.run_sync.assert_called_once_with(orm.Base.metadata.create_all)

    # check update
    assert len(mock_session.statements) == 1
