import asyncio
import logging
from typing import AsyncIterator, Iterator, Type, TypeVar

from bs4 import BeautifulSoup, Tag

import models
from . import data
from . import utils
from ..generic import ResultsScraper
from ..requester import HTTPClient, Limiter

__all__ = ["SportproScraper"]

logger = logging.getLogger(__name__)

limiter = Limiter(1)
client = HTTPClient()

RowType = TypeVar("RowType", bound=data.Row)


class SportproScraper(ResultsScraper):
    host = "https://www.sportpro.re"
    results_path = "/resultats/"
    
    def __init__(self):
        # collections of competitions scraped
        # when we scrap a single competition, a future is created and associated
        # to it in this dictionary
        self._scraping_tasks: dict[models.Competition, asyncio.Future | None] = {}

        # errors during each competition scraping
        # we collect them and log them at the end
        self._errors: list[Exception] = []

    async def scrap(self) -> AsyncIterator[models.Competition]:
        async with limiter:
            html = await client.get(f"{self.host}{self.results_path}")
        
        # find competitions and scrap the corresponding results
        for url, competition in self.__scrap_competitions(html):
            self._scraping_tasks[competition] = asyncio.ensure_future(self.__scrap_results(url, competition))

        logger.info(f"About to scrap results for {len(self._scraping_tasks)} competitions")
        while len(self._scraping_tasks) > 0:
            done = set()
            
            # find all competition that are scraped already
            for comp, fut in self._scraping_tasks.items():
                if fut.done():
                    try:
                        fut.result()
                        yield comp
                    except Exception as exc:
                        self._errors.append(exc)
                    done.add(comp)
            
            # remove the ones that are done
            for comp in done:
                del self._scraping_tasks[comp]
            
            # sleep 5 ms
            await asyncio.sleep(0.005)

        # handle errors
        if self._errors:
            logger.warning(f"{len(self._errors)} collected!")
    
    def __scrap_competitions(self, html: bytes) -> Iterator[tuple[str | None, models.Competition]]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find_all("table", attrs={"id": "resList"})[0]
        for row in self.__parse_table(table, data.CompetitionRow):
            competition = row.to_model()
            yield row.results_url, competition
            logger.debug(f"Successfully scraped competition={competition}")
    
    async def __scrap_results(self, url: str, competition: models.Competition):
        async with limiter:
            html = await client.get(utils.complete_url(self.host, url))
        soup = BeautifulSoup(html, "lxml")
        table = soup.find_all("table", attrs={"id": "resList"})[0]
        for row in self.__parse_table(table, data.ResultRow):
            try:
                competition.results.append(row.to_model())
            except:
                logger.exception(f"Error formatting row={row} (url={url})")
        logger.debug(
            f"Successfully scraped {len(competition.results)} results "
            f"for competition={competition}")
    
    @staticmethod
    def __parse_table(table: Tag, output: Type[data.Row]) -> Iterator[RowType]:
        """
        Parse an html table:
        - find the headers which will be the dictionaries keys
        - parse all rows and associate the found values to the headers as a dict
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
                    logger.debug(f"Error parsing row={row}")
                    continue
            res = output.from_dict(d)
            if res is not None and res.is_valid():
                yield res
