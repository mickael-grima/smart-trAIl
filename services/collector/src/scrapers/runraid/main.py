import logging
import re
from typing import AsyncIterator, Iterator

from bs4 import BeautifulSoup, Tag

import models
from . import parser, utils
from ..generic import MetadataScraper
from ..requester import HTTPClient, Limiter

__all__ = ["RunRaidScraper"]

logger = logging.getLogger(__name__)

limiter = Limiter(1)
client = HTTPClient()


class RunRaidScraper(MetadataScraper):
    """
    This scraper gets competitions details -> it is not meant to scrap results,
    since it is not a timekeeper
    """
    host = "http://runraid.free.fr"
    calendar_page = "/calendrier.php"

    all_competitions_title_regex = re.compile(
        r"Toutes les courses de pleine nature à la Réunion et Océan Indien en (?P<year>\d{4})")

    async def scrap(self) -> AsyncIterator[models.CompetitionMetaData]:
        async with limiter:
            html = await client.get(f"{self.host}{self.calendar_page}")

        soup = BeautifulSoup(html, "lxml")
        table, year = self.__find_table_and_year(soup)

        if table is not None:
            for row in self.__parse_table(table, year):
                yield row
                logger.debug(f"Successfully scraped competition={row}")

    def __find_table_and_year(
            self,
            soup: BeautifulSoup
    ) -> tuple[Tag | None, int | None]:
        """
        Find the table related to all competitions for current year
        """
        # first find the title
        for div in soup.find_all("div", attrs={"class": "Texte2"}):
            match = self.all_competitions_title_regex.match(div.text.strip(" \n"))
            if match is not None:
                year = match.groupdict()["year"]
                table = div.find_next("table", attrs={"class": "texte11"})
                return table, int(year)
        return None, None

    def __parse_table(self, table: Tag, year: int) -> Iterator[models.CompetitionMetaData]:
        """
        Parse a html table:
        - find the headers which will be the dictionaries keys
        - parse all rows and associate the found values to the headers as a dict
        """
        headers: list[str] = []
        for row in table.find_all("tr"):
            # everytime we encounter a header, we store it to better
            # extract the following rows
            if "center" in (row.get("align") or []):
                headers = [r.text for r in row.find_all("td")]
                continue

            # extract the row, and map its values to the headers
            d = {"Year": year}
            for i, column in enumerate(row.find_all("td")):
                try:
                    d[headers[i]] = column.text.strip(" \n")
                except (IndexError, KeyError, AttributeError):
                    logger.debug(f"Error parsing row={row}:column={i}")
                    continue

            for competition_row in self.__extract_competition_rows(d):
                yield competition_row

    @staticmethod
    def __extract_competition_rows(d: dict[str, str]) -> Iterator[models.CompetitionMetaData]:
        """
        Parse the data and create rows
        """
        dist_elevations = parser.parse_distance_and_elevation(
            d["Distance"],
            d["D +"],
            d["D -"],
        )
        for dist, pos_elevation, neg_elevation, year in dist_elevations:
            if year is None or year == d["Year"]:
                yield models.CompetitionMetaData(
                    date=models.Date(
                        start=utils.parse_date(f"{d['Date']}-{d['Year']}"),
                    ),
                    event=d["Course"],
                    place=d["Lieu"],
                    distance=dist,
                    positive_elevation=pos_elevation,
                    negative_elevation=neg_elevation,
                )
