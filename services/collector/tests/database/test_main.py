from contextlib import asynccontextmanager
from unittest.mock import patch, Mock

import pytest

from ..context import database


@pytest.fixture()
def client():
    @asynccontextmanager
    async def mock_client():
        yield "test"

    with patch("database.main.MySQLClient.client", mock_client):
        yield mock_client


@pytest.mark.asyncio
async def test_client(client):
    async with database.client() as c:
        assert c == "test"
