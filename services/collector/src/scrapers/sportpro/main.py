import asyncio
import logging
import time
from typing import AsyncIterator, Iterator

import models
from bs4 import BeautifulSoup, Tag

from . import utils
from ..generic import Scraper
from ..requester import HTTPClient, Limiter

logger = logging.getLogger(__name__)

limiter = Limiter(1)
client = HTTPClient()


class SportproScraper(Scraper):
    host = "https://www.sportpro.re"
    results_path = "/resultats/"
    
    # After this time (in second), we stop the scraping
    _timeout = 600
    
    def __init__(self):
        # collections of competitions scraped
        # when we scrap a single competition, a future is created and associated
        # to it in this dictionary
        self._scraping_tasks: dict[models.Competition, asyncio.Future | None] = {}

    async def scrap(self) -> AsyncIterator[models.Competition]:
        start = time.time()
        async with limiter:
            html = await client.get(f"{self.host}{self.results_path}")
        
        # find competitions and scrap the corresponding results
        for url, competition in self.__scrap_competitions(html):
            if url is None:
                continue
            self._scraping_tasks[competition] = asyncio.ensure_future(self.__scrap_results(url, competition))
        
        logger.debug(f"About to scrap results for {len(self._scraping_tasks)} competitions")
        while len(self._scraping_tasks) > 0:
            if time.time() - start >= self._timeout:
                logger.warning("Scraping took too long. Stop!")
                break
            
            done = set()
            
            # find all competition that are scraped already
            for comp, fut in self._scraping_tasks.items():
                if fut.done():
                    if isinstance(fut.result(), Exception):
                        try:
                            raise fut.result()
                        except:
                            logger.exception("Failure")
                    yield comp
                    done.add(comp)
            
            # remove the ones that are done
            for comp in done:
                del self._scraping_tasks[comp]
            
            # sleep 5 ms
            await asyncio.sleep(0.005)
    
    def __scrap_competitions(self, html: str) -> Iterator[tuple[str | None, models.Competition]]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find_all("table", attrs={"id": "resList"})[0]
        for row in self.__parse_table(table):
            competition = models.Competition(
                name=row["Compétition"],
                date=models.Date(
                    start=row["Date"]
                ),
                distance=utils.parse_distance(row["Distance"]),
            )
            yield row.get("Résultats"), competition
            logger.debug(f"Successfully scraped competition={competition}")
    
    async def __scrap_results(self, url: str, competition: models.Competition):
        async with limiter:
            html = await client.get(utils.complete_url(self.host, url))
        soup = BeautifulSoup(html, "lxml")
        table = soup.find_all("table", attrs={"id": "resList"})[0]
        for row in self.__parse_table(table):
            try:
                competition.results.append(models.Result(
                    time=utils.parse_time(row["Temps"]),
                    rank=models.Rank(
                        scratch=int(row["Scratch"]),
                        gender=int(row["Clst sexe"]),
                        category=int(row["Clst cat."]),
                    ),
                    runner=models.Runner(
                        first_name=row["Prénom"],
                        last_name=row["Nom"],
                        birth_year=int(row["Né(e)"]),
                        gender=utils.get_gender(row["Sexe"]),
                        license=row["Licence"],
                        category=row["Cat."],
                        race_number=row["Dossard"],
                    ),
                ))
            except (KeyError, ValueError):
                logger.exception("error extracting result")
                continue
        logger.debug(
            f"Successfully scraped {len(competition.results)} results "
            f"for competition={competition}")
    
    @staticmethod
    def __parse_table(table: Tag) -> Iterator[dict[str, str]]:
        """
        Parse an html table:
        - find the headers which will be the dictionaries keys
        - parse all rows and associate the found values to the headers as a dict
        """
        # first, find headers
        header = table.find_all("tr", attrs={"class": "header"})[0]
        keys = [r.text for r in header.find_all("th")]
        
        for row in table.find_all("tr")[1:]:
            data = {}
            for i, r in enumerate(row.find_all("td")):
                try:
                    if keys[i] == "Résultats":  # find the URL to the results page
                        data[keys[i]] = r.find_all("a")[0]["href"]
                    else:
                        data[keys[i]] = r.text
                except (IndexError, KeyError, AttributeError):
                    continue
            yield data
