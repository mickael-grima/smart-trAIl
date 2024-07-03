import datetime
import enum

import pydantic

import utils


class Gender(enum.Enum):
    male = "M"
    female = "F"
    undefined = "U"


class ResultStatus(enum.Enum):
    finisher = "finisher"
    abandoned = "abandoned"
    non_starter = "non-starter"
    disqualified = "disqualified"
    unknown = "unknown"


class Date(pydantic.BaseModel):
    start: datetime.date
    end: datetime.date | None = None


class Rank(pydantic.BaseModel):
    scratch: int
    gender: int
    category: int


class Runner(pydantic.BaseModel):
    first_name: str
    last_name: str
    birth_year: int | None = None
    gender: Gender


class Result(pydantic.BaseModel):
    runner: Runner
    time: datetime.timedelta | None = None
    rank: Rank | None = None
    status: ResultStatus
    race_number: int
    license: str | None = None
    category: str


class CompetitionMetaData(pydantic.BaseModel):
    event: str
    date: Date
    distance: float
    place: str | None = None
    positive_elevation: int | None = None
    negative_elevation: int | None = None

    def __similarity(self, metadata: "CompetitionMetaData") -> float:
        """
        Compare:
          - competition name
          - distance
          - positive elevation
          - negative elevation
          - date
        and return a score between 0 and 1.
        :return: a float between 0 and 1. 0 is no similarity, 1 is the maximum similarity
        """
        return (
            utils.distance_similarity(self.distance, metadata.distance, 2) *
            utils.distance_similarity(self.positive_elevation, metadata.positive_elevation, 200) *
            utils.distance_similarity(self.negative_elevation, metadata.negative_elevation, 200) *
            utils.distance_similarity(utils.hours_diff(self.date.start, metadata.date.start), 0, 4) *
            utils.string_similarity(self.event, metadata.event)
        )

    def find_best_match(
            self,
            all_competitions: dict[int, "CompetitionMetaData"],
            similarity_threshold: float = 0.85
    ) -> int | None:
        """
        Compare self to all competitions and return the id of the ones that
        matches at best
        """
        sim, comp_id = 0, None
        for cid, comp in all_competitions.items():
            s = self.__similarity(comp)
            if s < sim:
                continue
            sim = s
            comp_id = cid
        if sim >= similarity_threshold:
            return comp_id


class Competition(CompetitionMetaData):
    name: str
    timekeeper: str
    results: list[Result] = pydantic.Field(default_factory=list)

    def __hash__(self):
        return hash(f"{self.name}:{self.event}:{self.timekeeper}:{self.date.start}")
