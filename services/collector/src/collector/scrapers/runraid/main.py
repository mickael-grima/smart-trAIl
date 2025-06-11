import logging
import re
from collections.abc import AsyncIterator, Iterator

from bs4 import BeautifulSoup, Tag

from collector import models
from collector.scrapers.generic import MetadataScraper
from collector.scrapers.requester import HTTPClient, Limiter
from collector.scrapers.runraid import parser, utils

__all__ = ["RunRaidScraper"]

logger = logging.getLogger(__name__)

limiter = Limiter(1)
client = HTTPClient()


class RunRaidScraper(MetadataScraper):
    """
    RunRaidScraper gets competitions details.

    it is not meant to scrap results, since it is not a timekeeper.
    """

    host = "http://runraid.free.fr"
    calendar_page = "/calendrier.php"

    all_competitions_title_regex = re.compile(
        r"Toutes les courses de pleine nature à la Réunion et Océan Indien en "
        r"(?P<year>\d{4})")

    async def scrap(self) -> AsyncIterator[models.CompetitionMetaData]:
        """
        Scrap the competitions metadata from RunRaid website.

        Returns
        -------
        AsyncIterator[models.CompetitionMetaData]
            Iterate all competitions that were scrapped from the website.
        """
        async with limiter:
            html = await client.get(f"{self.host}{self.calendar_page}")

        soup = BeautifulSoup(html, "lxml")
        table, year = self.__find_table_and_year(soup)

        if table is not None:
            for row in self.__parse_table(table, year):
                yield row
                logger.debug("Successfully scraped competition=%s", row)

    def __find_table_and_year(
            self,
            soup: BeautifulSoup
    ) -> tuple[Tag | None, int | None]:
        """
        Find the html table related to all competitions for current year.

        Parameters
        ----------
        soup : BeautifulSoup
            The website html source code.

        Returns
        -------
        tuple[Tag | None, int | None]
            An html table containing all competitions to parse, and the year
            when those competitions happened. All competitions belong to the
            same year. If no table found, Non, None is returned instead.
        """
        # first find the title
        for div in soup.find_all("div", attrs={"class": "Texte2"}):
            match = self.all_competitions_title_regex.match(div.text.strip(" \n"))
            if match is not None:
                year = match.groupdict()["year"]
                table = div.find_next("table", attrs={"class": "texte11"})
                return table, int(year)
        return None, None

    def __parse_table(
            self, table: Tag, year: int) -> Iterator[models.CompetitionMetaData]:
        """
        Parse an html table containing all competitions for a given year.

        1. find the headers which will be the dictionaries keys.
        2. parse all rows and associate the found values to the headers as a
            dict.

        Parameters
        ----------
        table : Tag
            The html table containing all competitions, to parse.
        year : int
            The year when all those competitions happen.

        Returns
        -------
        Iterator[models.CompetitionMetaData]
            Iterate all competitions that were scrapped from the website.
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
                    logger.debug("Error parsing row=%s:column=%d", row, i)
                    continue

            yield from self.__extract_competition_rows(d)

    @staticmethod
    def __extract_competition_rows(
            d: dict[str, str]) -> Iterator[models.CompetitionMetaData]:
        """
        Convert the scrapped dict to a list of competition metadata.

        Parameters
        ----------
        d : dict[str, str]
            The scrapped competitions as a dictionary, originally a row in the
            scrapped html table. A single competition might have several events,
            so several competition metadata.

        Returns
        -------
        Iterator[models.CompetitionMetaData]
            Iterate all competitions metadata found from this html tables row.
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
