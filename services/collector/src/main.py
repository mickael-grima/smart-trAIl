import asyncio
import logging
import time

import models
from scrapers import SportproScraper
from database.mysql import Client as DBClient, add_competition

logger = logging.getLogger(__name__)


async def run():
    db = await DBClient.create()
    scraper = SportproScraper()

    # increment by 1 everytime a db update is started
    # decrement by 1 everytime a db update is finished
    n = 0

    async def store(comp: models.Competition):
        nonlocal n, db
        await add_competition(db, comp)
        n -= 1

    async for competition in scraper.scrap():
        n += 1
        asyncio.ensure_future(asyncio.create_task(store(competition)))

    log_time = time.time()
    while n > 0:
        if time.time() - log_time >= 10:
            logger.info(f"DATABASE update: {n} updates still on-going ...")
            log_time = time.time()
        await asyncio.sleep(0.01)


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    asyncio.run(run())
