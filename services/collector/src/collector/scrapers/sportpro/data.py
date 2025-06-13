import abc
import logging
from dataclasses import dataclass
from datetime import timedelta, date
from typing import Optional

from collector import models
from collector.scrapers.sportpro import utils

logger = logging.getLogger(__name__)


class Row(abc.ABC):
    """An abstract base class for a row of data."""

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, row: dict[str, str]) -> Optional["Row"]:
        """Create a Row from a dict."""

    def is_valid(self) -> bool:
        """Return true if the row is considered valid."""
        return True


@dataclass
class CompetitionRow(Row):
    """
    A competition row.

    Attributes
    ----------
    competition: str
        The competition's name
    date: date
        The date when the competition happens.
    distance: float
        How long this competition is.
    results_url: str
        The URL where to find this competition's results.
    event: str
        The competition's event name, if any.
    """

    competition: str
    date: date
    distance: float
    results_url: str | None
    event: str | None = None

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> "CompetitionRow":
        """Create a competition row from a dict."""
        return cls(
            competition=row["Compétition"],
            date=utils.parse_date(row["Date"]),
            distance=utils.parse_distance(row["Distance"]),
            results_url=row.get("Résultats"),
            event=row["Épreuve"],
        )

    def is_valid(self) -> bool:
        """Return true if the results url is provided."""
        return self.results_url is not None

    def to_model(self) -> models.Competition:
        """Transform this row into a competition model."""
        return models.Competition(
            timekeeper="sportpro",
            name=self.competition,
            event=self.event,
            date=models.Date(
                start=self.date
            ),
            distance=self.distance,
        )


@dataclass
class ResultRow(Row):
    """
    A result row.

    A result row is always linked to a single runner.
    Hence, we consider a result as an extension of a Runner.

    Attributes
    ----------
    license: str
        The runner's license
    category: str
        The runner's category: M0H, SEH, M1F, etc ...
    race_number: str
        The runner's race number.
    first_name: str
        The runner's first name.
    last_name: str
        The runner's last name.
    gender: str
        The runner's gender: M or F (or undefined)
    time: timedelta | None
        How much time did the runner take to complete the race. If the race
        wasn't completed for any reason, None is used.
    status: str
        The runner's race status: finisher, etc ...
    birth: int
        The runner's birth year.
    scratch: int | str | None
        The runner's scratch ranking. It should be an int if possible. In case
        the ranking parsing fails, we use the fetched value anyway.
    sex_ranking: int | str | None
        The runner's sex ranking. It should be an int if possible. In case
        the ranking parsing fails, we use the fetched value anyway.
    category_ranking: int | str | None
        The runner's category ranking. It should be an int if possible. In case
        the ranking parsing fails, we use the fetched value anyway.
    """

    license: str
    category: str
    race_number: str

    first_name: str
    last_name: str
    gender: str
    time: timedelta | None = None

    status: str = "finisher"
    birth: int | None = None

    scratch: int | str | None = None
    sex_ranking: int | None = None
    category_ranking: int | None = None

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> Optional["ResultRow"]:
        """Create a ResultRow from a dict."""
        try:
            if "Scratch" in row:
                # Case when the runner finished the race and has a ranking.
                return cls(
                    scratch=utils.cast_or_default(
                        row["Scratch"], int, default=row["Scratch"]),
                    sex_ranking=utils.cast_or_default(row["Clst sexe"], int),
                    category_ranking=utils.cast_or_default(
                        row["Clst cat."], int),
                    license=row["Licence"],
                    category=row["Cat."],
                    race_number=row["Dossard"],
                    first_name=row["Prénom"],
                    last_name=row["Nom"],
                    birth=utils.cast_or_default(row['Né(e)'], int),
                    gender=row["Sexe"],
                    time=utils.parse_time(row["Temps"])
                )
            # The runner didn't finish the race and hasn't any ranking.
            return cls(
                status=row[""],
                license=row["Licence"],
                category=row["Cat."],
                race_number=row["Dossard"],
                first_name=row["Prénom"],
                last_name=row["Nom"],
                birth=utils.cast_or_default(row['Né(e)'], int),
                gender=row["Sexe"],
            )
        except (KeyError, ValueError):
            logger.exception("error extracting result from row=%s", row)

    def is_valid(self) -> bool:
        """Return true if a birth is provided."""
        return self.birth is not None

    def to_model(self) -> models.Result:
        """Transform this row into a Result model."""
        rank: models.Rank | None = None
        status = self.get_status()
        if status == models.ResultStatus.FINISHER:
            rank = models.Rank(
                scratch=self.scratch,
                gender=self.sex_ranking,
                category=self.category_ranking,
            )
        return models.Result(
            time=self.time,
            status=status,
            rank=rank,
            license=self.license,
            category=self.category,
            race_number=self.race_number,
            runner=models.Runner(
                first_name=self.first_name,
                last_name=self.last_name,
                birth_year=self.birth,
                gender=models.Gender(self.gender),
            ),
        )

    def get_status(self) -> models.ResultStatus:
        """Convert the scrapped status into a more readable one (in english)."""
        match self.status:
            case "finisher":
                return models.ResultStatus.FINISHER
            case "Abandon":
                return models.ResultStatus.ABANDONED
            case "Non partant":
                return models.ResultStatus.NON_STARTER
            case "Disqualification":
                return models.ResultStatus.DISQUALIFIED
            case "":
                return models.ResultStatus.UNKNOWN
            case _:
                logger.warning(
                    "Unknown status=\"%s\" from row=%s", self.status, self)
                return models.ResultStatus.UNKNOWN
