from contextlib import asynccontextmanager, AbstractAsyncContextManager

from collector.database.generic import Database
from collector.database.mysql import Client as MySQLClient

__all__ = ["client"]


@asynccontextmanager
async def client() -> AbstractAsyncContextManager[Database]:
    """Yield a database client."""
    async with MySQLClient.client() as c:
        yield c
