import asyncio
import logging
import time

from scrapers import discover as discover_scrapers, Scraper
from database import client as db_client, Database
from controller import BackgroundController

logger = logging.getLogger(__name__)


async def run_single(scraper: Scraper, db: Database):
    controller = BackgroundController()

    async for competition in scraper.scrap():
        controller.run_in_background(db.add_competition(competition))

    log_time = time.time()
    while controller.running:
        # log progress every 10 seconds
        if time.time() - log_time >= 10:
            logger.info(
                f"DATABASE update: {controller.number_background_tasks} "
                f"updates still on-going ...")
            log_time = time.time()
        await asyncio.sleep(0.01)


async def run():
    async with db_client() as db:
        await asyncio.gather(*[
            run_single(scraper, db)
            for scraper in discover_scrapers()
        ])


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    asyncio.run(run())
