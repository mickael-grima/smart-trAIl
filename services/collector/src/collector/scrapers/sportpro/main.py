import asyncio
import logging
from collections.abc import AsyncIterator, Iterator
from typing import TypeVar

from bs4 import BeautifulSoup, Tag

from collector import models
from collector.scrapers.generic import ResultsScraper
from collector.scrapers.requester import HTTPClient, Limiter
from collector.scrapers.sportpro import data
from collector.scrapers.sportpro import utils

__all__ = ["SportproScraper"]

logger = logging.getLogger(__name__)

limiter = Limiter(1)
client = HTTPClient()

RowType = TypeVar("RowType", bound=data.Row)


class SportproScraper(ResultsScraper):
    """SportPro Scraper."""

    host = "https://www.sportpro.re"
    results_path = "/resultats/"

    def __init__(self) -> None:
        # collections of competitions scraped
        # when we scrap a single competition, a future is created and associated
        # to it in this dictionary
        self._scraping_tasks: dict[models.Competition, asyncio.Future | None] = {}

        # errors during each competition scraping
        # we collect them and log them at the end
        self._errors: list[Exception] = []

    async def scrap(self) -> AsyncIterator[models.Competition]:
        """
        Scrap the sportpro results page.

        Returns
        -------
        AsyncIterator[models.Competition]
            An iterator of all scraped competitions from the website.
        """
        async with limiter:
            html = await client.get(f"{self.host}{self.results_path}")

        # find competitions and scrap the corresponding results
        for url, competition in self.__scrap_competitions(html):
            self._scraping_tasks[competition] = asyncio.ensure_future(
                self.__scrap_results(url, competition))

        logger.info(
            "About to scrap results for %d competitions",
            len(self._scraping_tasks))
        while len(self._scraping_tasks) > 0:
            done = set()

            # find all competition that are scraped already
            for comp, fut in self._scraping_tasks.items():
                if fut.done():
                    try:
                        fut.result()
                        yield comp
                    except Exception as exc:  # noqa: BLE001
                        self._errors.append(exc)
                    done.add(comp)

            # remove the ones that are done
            for comp in done:
                del self._scraping_tasks[comp]

            # sleep 5 ms
            await asyncio.sleep(0.005)

        # handle errors
        if self._errors:
            logger.warning("%d collected!", len(self._errors))

    def __scrap_competitions(
            self,
            html: bytes
    ) -> Iterator[tuple[str | None, models.Competition]]:
        """Parse html page into a competition model and its URL."""
        soup = BeautifulSoup(html, "lxml")
        table = soup.find_all("table", attrs={"id": "resList"})[0]
        for row in self.__parse_table(table, data.CompetitionRow):
            competition = row.to_model()
            yield row.results_url, competition
            logger.debug("Successfully scraped competition=%s", competition)

    async def __scrap_results(
            self, url: str, competition: models.Competition) -> None:
        """
        Extract results from the html page under url.

        Add the fetched results into `competition`.

        Parameters
        ----------
        url : str
            The URL where the results can be found.
        competition: models.Competition
            The competition to which the results belong. Fetched results are
            added to this competition.
        """
        async with limiter:
            html = await client.get(utils.complete_url(self.host, url))
        soup = BeautifulSoup(html, "lxml")
        table = soup.find_all("table", attrs={"id": "resList"})[0]
        for row in self.__parse_table(table, data.ResultRow):
            try:
                competition.results.append(row.to_model())
            except Exception:
                logger.exception("Error formatting row=%s (url=%s)",  row, url)
        logger.debug(
            "Successfully scraped %d results for competition=%s",
            len(competition.results), competition)

    @staticmethod
    def __parse_table(table: Tag, output: type[data.Row]) -> Iterator[RowType]:
        """
        Parse an html table.

        1. find the headers which will be the dictionaries keys
        2. parse all rows and associate the found values to the headers as a
            dict.

        Parameters
        ----------
        table : Tag
            HTML table to parse.
        output : type[data.Row]
            The output wrapper for each table's row that are scraped.

        Returns
        -------
        Iterator[RowType]
            Iterate the scraped rows from the table.
        """
        headers: list[str] = []
        for row in table.find_all("tr"):
            # everytime we encounter a header, we store it to better
            # extract the following rows
            if "header" in (row.get("class") or []):
                headers = [r.text for r in row.find_all("th")]
                continue

            # extract the row, and map its values to the headers
            d = {}
            # needed for colspan attributes, to target the right header
            offset: int = 0
            for i, column in enumerate(row.find_all("td")):
                # too many entries compared to the current headers
                if i >= len(headers):
                    break
                header = headers[i + offset]
                # update offset
                offset += int(column.get("colspan", "1")) - 1
                try:
                    if header == "Résultats":  # find the URL to the results page
                        d[header] = column.find_all("a")[0]["href"]
                    else:
                        d[header] = column.text
                except (IndexError, KeyError, AttributeError):
                    logger.debug("Error parsing row=%s", row)
                    continue
            res = output.from_dict(d)
            if res is not None and res.is_valid():
                yield res
