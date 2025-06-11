import asyncio
from collections.abc import Callable
from contextlib import asynccontextmanager
from unittest.mock import patch, Mock, AsyncMock

import aiohttp
import pytest

from collector.scrapers import requester


@pytest.fixture
def mock_session() -> Callable[[int, str | Exception], Mock]:
    """Mock an aiohttp session object."""

    def get_session(status: int, expected: str | Exception) -> Mock:
        _session = Mock()
        _session.nb_get_calls = 0

        @asynccontextmanager
        async def get(*args, **kwargs):
            _session.nb_get_calls += 1
            res = Mock()
            res.status = status
            res.raise_for_status.side_effect = (
                aiohttp.ClientError() if isinstance(expected, Exception) else
                expected
            )
            res.read = AsyncMock(return_value=expected)
            yield res

        _session.get = get
        return _session

    return get_session


class TestHTTPClient:
    @pytest.mark.parametrize(
        "status,nb_get_calls,expected",
        [
            (200, 1, "test"),
            (429, 4, requester.HTTPError(status=429)),
            (500, 1, requester.HTTPError(status=500))
        ]
    )
    @pytest.mark.asyncio
    async def test_get(
            self,
            status: int,
            nb_get_calls: int,
            expected: Exception | str,
            mock_session: Callable[[int, str | Exception], Mock]
    ):
        session = mock_session(status, expected)
        url = "http://example.com"

        with patch("aiohttp.ClientSession", return_value=session):
            client = requester.HTTPClient()
            if isinstance(expected, requester.HTTPError):
                with pytest.raises(expected.__class__) as exc:
                    await client.get(url)
                assert exc.type is requester.HTTPError
            else:
                assert await client.get(url) == expected
            assert session.nb_get_calls == nb_get_calls


class TestLimiter:
    @pytest.mark.asyncio
    async def test_as_decorator(self):
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
    async def test_as_context_manager(self):
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
