from contextlib import asynccontextmanager
from typing import AsyncContextManager

from .mysql import Client as MySQLClient
from .generic import Database

__all__ = ["session"]


@asynccontextmanager
async def session() -> AsyncContextManager[Database]:
    return MySQLClient.session()
