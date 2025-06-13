import datetime
import enum

import pydantic

from collector import utils


@enum.unique
class Gender(enum.StrEnum):
    """Gender possibilities."""

    MALE = "M"
    FEMALE = "F"
    UNDEFINED = "U"


@enum.unique
class ResultStatus(enum.StrEnum):
    """Race result statuses."""

    FINISHER = "finisher"
    ABANDONED = "abandoned"
    NON_STARTER = "non-starter"
    DISQUALIFIED = "disqualified"
    UNKNOWN = "unknown"


class Date(pydantic.BaseModel):
    """
    Date model, with a start and end date.

    Attributes
    ----------
    start : datetime.date
        Required. The start-date of the race.
    end: datetime.date
        Optional. The end-date of the race. If not provided, the start date is
        used.
    """

    start: datetime.date
    end: datetime.date | None = None


class Rank(pydantic.BaseModel):
    """
    The runner's race's ranking.

    Attributes
    ----------
    scratch: int
        The scratch ranking.
    gender: int
        The gender ranking.
    category: int
        The category's ranking.
    """

    scratch: int
    gender: int
    category: int


class Runner(pydantic.BaseModel):
    """
    Runner's data.

    Attributes
    ----------
    first_name: str
        First name of the runner.
    last_name: str
        Last name of the runner.
    birth_year: int
        Birth year of the runner.
    gender: Gender
        The gender of the runner.
    """

    first_name: str
    last_name: str
    birth_year: int | None = None
    gender: Gender


class Result(pydantic.BaseModel):
    """Runner's result for a given race."""

    runner: Runner
    time: datetime.timedelta | None = None
    rank: Rank | None = None
    status: ResultStatus
    race_number: int
    license: str | None = None
    category: str


class CompetitionMetaData(pydantic.BaseModel):
    """Competition meta-data."""

    event: str
    date: Date
    distance: float
    place: str | None = None
    positive_elevation: int | None = None
    negative_elevation: int | None = None

    def __similarity(self, metadata: "CompetitionMetaData") -> float:
        """
        Return the similarity score between 2 competitions.

        Compare:
          - competition name
          - distance
          - positive elevation
          - negative elevation
          - date
        and return a score between 0 and 1.

        Returns
        -------
        float
            a float between 0 and 1. 0 is no similarity, 1 is the maximum
            similarity.
        """
        return (
            utils.distance_similarity(
                self.distance,
                metadata.distance,
                perc90_delta=2) *
            utils.distance_similarity(
                self.positive_elevation,
                metadata.positive_elevation,
                perc90_delta=200) *
            utils.distance_similarity(
                self.negative_elevation,
                metadata.negative_elevation,
                perc90_delta=200) *
            utils.distance_similarity(
                utils.hours_diff(self.date.start, metadata.date.start),
                0,
                perc90_delta=4) *
            utils.sentence_similarity(self.event, metadata.event)
        )

    def find_best_match(
            self,
            all_competitions: dict[int, "CompetitionMetaData"],
            similarity_threshold: float = 0.85
    ) -> int | None:
        """
        Find the best match in all given competitions.

        Compare self to all competitions and return the id of the ones that
        matches at best

        Parameters
        ----------
        all_competitions: dict[int, CompetitionMetaData]
            A mapping id -> competition, of all competitions to be compared
            with self.
        similarity_threshold: float
            Only consider competitions whose similarity score is at least this
            threshold. If no competitions meets this minimum, None is returned.

        Returns
        -------
        int
            The competition id which has the best match, respecting the minimum
            threshold.
        """
        sim, comp_id = 0, None
        for cid, comp in all_competitions.items():
            s = self.__similarity(comp)
            if s < sim:
                continue
            sim = s
            comp_id = cid
        return comp_id if sim >= similarity_threshold else None


class Competition(CompetitionMetaData):
    """Competition data."""

    name: str
    timekeeper: str
    results: list[Result] = pydantic.Field(default_factory=list)

    def __hash__(self) -> int:
        """Return a unique id for this competition."""
        return hash(
            f"{self.name}:{self.event}:{self.timekeeper}:{self.date.start}")
