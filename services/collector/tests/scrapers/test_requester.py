import asyncio
from contextlib import asynccontextmanager
from unittest.mock import patch, Mock, AsyncMock

import aiohttp
import pytest

from ..context import scrapers
from scrapers import requester


@pytest.mark.parametrize(
    "status,nb_get_calls,expected",
    [
        (200, 1, "test"),
        (429, 4, requester.HTTPException(status=429)),
        (500, 1, requester.HTTPException(status=500))
    ]
)
@pytest.mark.asyncio
async def test_HTTPClient_get(
        status: int,
        nb_get_calls: int,
        expected: Exception | str
):
    session = Mock()
    session.nb_get_calls = 0

    @asynccontextmanager
    async def get(*args, **kwargs):
        session.nb_get_calls += 1
        res = Mock()
        res.status = status
        res.raise_for_status.side_effect = (
            aiohttp.ClientError() if isinstance(expected, Exception) else
            expected
        )
        res.text = AsyncMock(return_value=expected)
        yield res

    session.get = get

    with patch("aiohttp.ClientSession", return_value=session):
        client = requester.HTTPClient()
        url = "http://example.com"
        if isinstance(expected, Exception):
            with pytest.raises(expected.__class__) as exc:
                try:
                    await client.get(url)
                except Exception as e:
                    assert e.status == status
                    raise
            assert exc.type is requester.HTTPException
        else:
            assert await client.get(url) == expected
        assert session.nb_get_calls == nb_get_calls


@pytest.mark.asyncio
async def test_Limiter_as_decorator():
    limiter = requester.Limiter(3)
    limiter.release_time = 0.01
    counter = 0

    @limiter
    async def count():
        nonlocal counter
        counter += 1

    for _ in range(5):
        asyncio.ensure_future(count())

    # 3 first calls are immediate
    await asyncio.sleep(0)
    assert counter == 3

    # locks not released yet: not more counter added
    await asyncio.sleep(limiter.release_time * 9 / 10)
    assert counter == 3

    # locks released
    await asyncio.sleep(limiter.release_time * 2 / 10)
    assert counter == 5


@pytest.mark.asyncio
async def test_Limiter_as_context_manager():
    limiter = requester.Limiter(3)
    limiter.release_time = 0.01
    counter = 0

    async def count():
        nonlocal counter
        async with limiter:
            counter += 1

    for _ in range(5):
        asyncio.ensure_future(count())

    # 3 first calls are immediate
    await asyncio.sleep(0)
    assert counter == 3

    # locks not released yet: not more counter added
    await asyncio.sleep(limiter.release_time * 9 / 10)
    assert counter == 3

    # locks released
    await asyncio.sleep(limiter.release_time * 2 / 10)
    assert counter == 5
