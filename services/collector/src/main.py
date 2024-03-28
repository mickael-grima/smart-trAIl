import asyncio
import logging

from scrapers import SportproScraper


async def run():
    scraper = SportproScraper()
    competitions = [c async for c in scraper.scrap()]
    print(competitions[0])


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(run())
