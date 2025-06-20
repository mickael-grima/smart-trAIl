import argparse
import asyncio
import logging

from collector.controller import BackgroundController
from collector.database import client as db_client, Database
from collector.scrapers import (
    discover_timekeepers as discover_timekeepers_scrapers,
    discover_metadata_scrapers,
    ResultsScraper,
    MetadataScraper
)

logger = logging.getLogger(__name__)

scrap_all_type = 'all'
scrap_timekeepers_type = 'timekeepers'
scrap_metadata_type = 'metadata'


async def run_single_results_scraper(scraper: ResultsScraper, db: Database) -> None:
    """
    Run a single scraper.

    Run `scraper.scrap()` function to iterate all found competition events
    and the results
    Concurrently, add those data in the DB

    :param scraper: the scraper that will iterate competitions and results
    :param db: the database client
    """
    controller = BackgroundController()

    async for competition in scraper.scrap():
        controller.run_in_background(db.add_competition(competition))

    await controller.wait()


async def run_metadata_scraper(scraper: MetadataScraper, db: Database) -> None:
    """
    Run the scraper to fetch metadata.

    Execute `scraper.scrap()` to iterate a set of events' metadata
    Then, concurrently, update the DB events with those metadata

    :param scraper: the scraper that will iterate competition events' metadata
    :param db: the database client
    """
    controller = BackgroundController()
    all_competitions = await db.search_competitions()

    async for metadata in scraper.scrap():
        comp_id = metadata.find_best_match(all_competitions)
        if comp_id is None:
            logger.debug("%s has a no best match", metadata.event)
            continue
        logger.debug(
            "%s has a best match: %s",
            metadata.event,
            all_competitions[comp_id].event)
        controller.run_in_background(db.update_competition(comp_id, metadata))

    await controller.wait()


async def run(
        type_: str = scrap_all_type,
        scrapers: list[str] | None = None
) -> None:
    """Run all scrapers."""
    # set-up logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    async with db_client() as db:
        if type_ in {scrap_all_type, scrap_timekeepers_type}:
            # first fetch the data from timekeepers
            await asyncio.gather(*[
                run_single_results_scraper(scraper, db)
                for scraper in discover_timekeepers_scrapers(scrapers=scrapers)
            ])
        if type_ in {scrap_all_type, scrap_metadata_type}:
            # then fetch metadata (elevations for example)
            await asyncio.gather(*[
                run_metadata_scraper(scraper, db)
                for scraper in discover_metadata_scrapers(scrapers=scrapers)
            ])


if __name__ == '__main__':
    # parse args
    parser = argparse.ArgumentParser(description='Define what scraper(s) to run')
    parser.add_argument(
        '-t', '--type',
        choices=[scrap_all_type, scrap_metadata_type, scrap_timekeepers_type],
        default=scrap_all_type,
        help='What kind of scrapers do we run: timekeepers, metadata, or both?'
    )
    parser.add_argument(
        '-s', '--scrapers',
        default='',
        help='comma-separated list of scrapers to run.'
    )
    args = parser.parse_args()

    # run
    asyncio.run(run(type_=args.type, scrapers=args.scrapers or None))
