import asyncio
from collections.abc import Coroutine


class BackgroundController:
    """
    Handles in background the async futures.

    It provides:
    - a method to run an async method in background (not blocking).
    - a method to wait until all tasks are done.
    """

    def __init__(self) -> None:
        # each background task has a related event.
        # only when all events are set can we consider all the tasks done.
        self.__events: set[asyncio.Event] = set()
        # Store all the created background tasks
        self.__tasks: set[asyncio.Task] = set()

    async def wait(self) -> None:
        """Wait until all stored tasks are complete."""
        await asyncio.wait(self.__tasks)

    def run_in_background(self, cor: Coroutine) -> None:
        """
        Start the passed coroutine as a background task.

        Parameters
        ----------
        cor : Coroutine
        """
        self.__tasks.add(
            asyncio.ensure_future(asyncio.create_task(self.__run(cor))))

    async def __run(self, cor: Coroutine) -> None:
        """Create an event and await the coroutine `coro`."""
        event = asyncio.Event()
        self.__events.add(event)
        try:
            await cor
        finally:
            event.set()
