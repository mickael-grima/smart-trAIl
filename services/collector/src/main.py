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

    while controller.running:
        await asyncio.sleep(0.01)


async def run():
    # set-up logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    async with db_client() as db:
        await asyncio.gather(*[
            run_single(scraper, db)
            for scraper in discover_scrapers()
        ])


if __name__ == '__main__':
    asyncio.run(run())
