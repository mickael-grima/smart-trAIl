import asyncio
import logging
from collections.abc import Callable, Awaitable
from http import HTTPStatus
from http.client import responses

import aiohttp

logger = logging.getLogger(__name__)


class HTTPError(Exception):
    """Custom HTTP Exception with the http status code."""

    def __init__(self, status: int = 200) -> None:
        self._status = status

    @property
    def status(self) -> int:
        """Return the http status code."""
        return self._status


class HTTPClient:
    """Implement an HTTP client."""

    def __init__(self, nb_retries: int = 3) -> None:
        # Maximum number of retries if failure.
        self._nb_retries = nb_retries
        # The HTTP session.
        self._session: aiohttp.ClientSession | None = None

    def __del__(self) -> None:
        """Close the http session."""
        if self._session is not None:
            self._session._connector._close()  # noqa: SLF001

    def __initialize_session(self) -> None:
        """
        Initialize the http session.

        The session should be initialized inside the running loop context.
        """
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                verify_ssl=False,
            ),
            timeout=aiohttp.ClientTimeout(10),
            trust_env=True,
        )

    async def get(
            self,
            url: str,
            params: dict[str, str] | None = None,
            retry_no: int = 0
    ) -> bytes:
        """
        Send a GET request.

        Send a request to URL, and fetch its response's body to return it
        Response status code are handled and logged accordingly

        Parameters
        ----------
        url: str
            requested url.
        params: dict[str, str]
            dict of query parameters
        retry_no: int
            how many tries we already retried before

        Returns
        -------
        bytes
            The response body.
        """
        if self._session is None:
            self.__initialize_session()
        status: int = -1
        logger.debug("Starting request to %s ...", url)
        try:
            async with self._session.get(url, params=params) as resp:
                status = resp.status
                resp.raise_for_status()
                return await resp.read()
        except aiohttp.ClientError as e:
            if status == HTTPStatus.TOO_MANY_REQUESTS:
                if retry_no >= self._nb_retries:
                    raise HTTPError(status=status) from e
                return await self.get(url, params=params, retry_no=retry_no + 1)
            raise HTTPError(status=status) from e
        finally:
            msg = f"\"GET {url}\" {status}"
            if status >= 0:
                msg += f" {responses[status]}"
            logger.info(msg, extra={
                "method": "GET",
                "url": url,
                "status_code": status,
            })


class Limiter:
    """
    Limit the number of concurrent requests.

    This is based on a semaphore. Only a given amount of request can go in
    parallel, and the lock is released after 1 second.

    Used to limit the rqs for a given website.

    Attributes
    ----------
    release_time: int
        Ho long to wait until the lock is released.
    """

    release_time = 1  # 1sec

    def __init__(self, rqs: int) -> None:
        # how many request per second allowed
        self._sem = asyncio.Semaphore(rqs)
        # keep a reference of the background tasks
        self.__releasing_tasks: set[asyncio.Future] = set()

    async def __acquire_call(self) -> None:
        """
        Acquire a call during 1 second.

        Releasing the semaphore is done in background independently on the
        status of any other tasks.
        """
        await self._sem.acquire()

        async def release() -> None:
            """Release 1 unit of the semaphore."""
            await asyncio.sleep(self.release_time)
            self._sem.release()

        # run the task in background
        task = asyncio.ensure_future(asyncio.shield(release()))
        self.__releasing_tasks.add(task)
        task.add_done_callback(self.__releasing_tasks.discard)

    def __call__(self, func: Callable[[...], Awaitable]) -> Callable:
        """
        Act as a decorator.

        Acquire a lock and release it in background after a sec.
        """
        async def wrapper(*args, **kwargs) -> Awaitable:  # noqa: ANN003,ANN002
            await self.__acquire_call()
            return await func(*args, **kwargs)
        return wrapper

    async def __aenter__(self) -> None:
        """Acquire the lock."""
        await self.__acquire_call()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Nothing done here when leaving the context."""
