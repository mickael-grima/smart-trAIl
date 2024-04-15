import asyncio

import pytest

from .context import controller


@pytest.mark.asyncio
async def test_BackgroundController():
    c = controller.BackgroundController()

    # no background tasks yet
    assert c.number_background_tasks == 0
    assert c.running is False

    async def run(t: int):
        await asyncio.sleep(t / 1000.)

    c.run_in_background(run(5))  # sleep 5 ms
    c.run_in_background(run(10))  # sleep 10ms
    c.run_in_background(run(2))  # sleep 2ms

    assert c.number_background_tasks == 3
    assert c.running is True

    # wait 1 ms -- everything still running
    await asyncio.sleep(0.001)
    assert c.number_background_tasks == 3
    assert c.running is True

    # wait 2 ms -- 1 finished
    await asyncio.sleep(0.002)
    assert c.number_background_tasks == 2
    assert c.running is True

    # wait 3 ms -- 2 finished
    await asyncio.sleep(0.003)
    assert c.number_background_tasks == 1
    assert c.running is True

    # wait 5 ms -- 2 finished
    await asyncio.sleep(0.005)
    assert c.number_background_tasks == 0
    assert c.running is False
