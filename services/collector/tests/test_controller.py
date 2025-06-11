import asyncio

import pytest

from collector import controller


class TestBackgroundController:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        results: list[int] = []  # store run results
        c = controller.BackgroundController()

        async def run(t: int):
            await asyncio.sleep(t / 1000.)
            results.append(t)

        c.run_in_background(run(5))  # sleep 5 ms
        c.run_in_background(run(10))  # sleep 10ms
        c.run_in_background(run(2))  # sleep 2ms

        # wait 1 ms -- everything still running
        await asyncio.sleep(0.001)
        assert results == []

        # wait 2 ms -- 1 finished
        await asyncio.sleep(0.002)
        assert results == [2]

        # wait 3 ms -- 2 finished
        await asyncio.sleep(0.003)
        assert results == [2, 5]

        # wait 5 ms -- 2 finished
        await asyncio.sleep(0.005)
        assert results == [2, 5, 10]
