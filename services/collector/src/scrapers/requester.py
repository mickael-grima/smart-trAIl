import asyncio
import logging
from http.client import responses

import aiohttp

logger = logging.getLogger(__name__)


class HTTPClient:
    def __init__(self, nb_retries: int = 3):
        self._nb_retries = nb_retries
        self._session: aiohttp.ClientSession | None = None
    
    def __del__(self):
        if self._session is not None:
            self._session._connector._close()
    
    def __initialize_session(self):
        """
        The session should be initialized inside the running loop context
        """
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                verify_ssl=False,
            ),
            timeout=aiohttp.ClientTimeout(10),
            trust_env=True,
        )

    async def get(self, url: str, params: dict = None, retry_no: int = 0) -> str:
        """
        Send a request to URL, and fetch its response's body to return it
        Response status code are handled and logged accordingly
        
        :param url: requested url
        :param params: dict of query parameters
        :param retry_no: how many tries we already retried before
        """
        if self._session is None:
            self.__initialize_session()
        status: int = -1
        logger.debug(f"Starting request to {url} ...")
        try:
            async with self._session.get(url, params=params) as resp:
                status = resp.status
                resp.raise_for_status()
                return await resp.text()
        except aiohttp.ClientError:
            if status == 429:
                if retry_no >= self._nb_retries:
                    logger.exception(f"Too many requests, even after {retry_no} retries")
                    raise
                return await self.get(url, params=params, retry_no=retry_no + 1)
            logger.exception(f"Failed with status={status}")
            raise
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
    def __init__(self, rqs: int):
        """
        :param rqs: how many request per second allowed
        """
        self._sem = asyncio.Semaphore(rqs)
    
    async def __acquire_call(self):
        """
        acquire a call during 1sec
        releasing the semaphore is done in background
        independently on the status of any other tasks
        """
        await self._sem.acquire()

        async def release():
            await asyncio.sleep(1)
            self._sem.release()

        asyncio.ensure_future(asyncio.shield(release()))
    
    def __call__(self, func):
        """
        Act as a decorator
        Acquire a lock and release it in background after a sec
        """
        async def wrapper(*args, **kwargs):
            await self.__acquire_call()
            return await func(*args, **kwargs)
        return wrapper
    
    async def __aenter__(self):
        await self.__acquire_call()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
