import abc
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import models
from . import utils

logger = logging.getLogger(__name__)


class Row(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_dict(cls, row: dict[str, str]) -> Optional["Row"]:
        """Create a Row from a dict"""

    def is_valid(self) -> bool:
        return True


@dataclass
class CompetitionRow(Row):
    competition: str
    date: datetime.date
    distance: float
    results_url: str | None
    event: str | None = None

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> "CompetitionRow":
        return cls(
            competition=row["Compétition"],
            date=utils.parse_date(row["Date"]),
            distance=utils.parse_distance(row["Distance"]),
            results_url=row.get("Résultats"),
            event=row["Épreuve"],
        )

    def is_valid(self) -> bool:
        return self.results_url is not None

    def to_model(self) -> models.Competition:
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
    license: str
    category: str
    race_number: str

    first_name: str
    last_name: str
    gender: str
    time: Optional[datetime.time] = None

    status: str = "finisher"
    birth: int | None = None

    scratch: int | str | None = None
    sex_ranking: int | None = None
    category_ranking: int | None = None

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> Optional["ResultRow"]:
        try:
            if "Scratch" in row:
                return cls(
                    scratch=utils.cast_or_default(row["Scratch"], int, default=row["Scratch"]),
                    sex_ranking=utils.cast_or_default(row["Clst sexe"], int),
                    category_ranking=utils.cast_or_default(row["Clst cat."], int),
                    license=row["Licence"],
                    category=row["Cat."],
                    race_number=row["Dossard"],
                    first_name=row["Prénom"],
                    last_name=row["Nom"],
                    birth=utils.cast_or_default(row['Né(e)'], int),
                    gender=row["Sexe"],
                    time=utils.parse_time(row["Temps"])
                )
            else:  # not finisher
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
            logger.exception(f"error extracting result from row={row}")

    def is_valid(self) -> bool:
        if self.birth is None:
            return False
        return True

    def to_model(self) -> models.Result:
        rank: models.Rank | None = None
        status = self.get_status()
        if status == models.ResultStatus.finisher:
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
                gender=utils.get_gender(self.gender),
            ),
        )

    def get_status(self) -> models.ResultStatus:
        match self.status:
            case "finisher":
                return models.ResultStatus.finisher
            case "Abandon":
                return models.ResultStatus.abandoned
            case "Non partant":
                return models.ResultStatus.non_starter
            case "Disqualification":
                return models.ResultStatus.disqualified
            case "":
                return models.ResultStatus.unknown
            case _:
                logger.warning(f"Unknown status=\"{self.status}\" from row={self}")
                return models.ResultStatus.unknown
