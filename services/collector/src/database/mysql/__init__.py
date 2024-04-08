import asyncio
import logging

import models
from .client import MySQLClient as Client

logger = logging.getLogger(__name__)


async def add_competition(db: Client, competition: models.Competition):
    # first add competitions and runners, and collect their db ids
    runners = [result.runner for result in competition.results]
    ids = await asyncio.gather(
        db.add_competition_event(competition),
        *[db.add_runner(runner) for runner in runners]
    )

    # get competition id and runners ids
    event_id = ids[0]
    runner_ids = [rid for rid in ids[1:]]

    # map competition.id & runner.id to its result
    results: dict[int, models.Result] = {}
    for j, result in enumerate(competition.results):
        runner_id = runner_ids[j]
        if runner_id is None:
            logger.warning(f"Missing runner id for result={result}")
            continue
        results[runner_id] = result

    # store results
    if results:
        await db.add_competition_results(event_id, results)
