from contextlib import asynccontextmanager
from typing import AsyncContextManager

from .mysql import Client as MySQLClient
from .generic import Database

__all__ = ["client"]


@asynccontextmanager
async def client() -> AsyncContextManager[Database]:
    async with MySQLClient.client() as c:
        yield c
