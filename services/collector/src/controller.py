import asyncio
from typing import Coroutine

from database import Database


class BackgroundController:
    def __init__(self):
        # number of running coroutines in background
        self._n = 0

    @property
    def number_background_tasks(self) -> int:
        return self._n

    @property
    def running(self) -> bool:
        """
        True if at least 1 coroutine is still running in background
        """
        return self.number_background_tasks > 0

    def run_in_background(self, cor: Coroutine):
        """
        Start the passed coroutine as a background task,
        and increment self._n
        """
        self._n += 1
        asyncio.ensure_future(asyncio.create_task(self.__run(cor)))

    async def __run(self, cor: Coroutine):
        try:
            await cor
        finally:
            self._n -= 1
