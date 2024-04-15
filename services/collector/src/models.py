import datetime
import enum

import pydantic


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


class Competition(pydantic.BaseModel):
    name: str
    event: str
    timekeeper: str
    date: Date
    distance: float
    results: list[Result] = pydantic.Field(default_factory=list)

    def __hash__(self):
        return hash(f"{self.name}:{self.event}:{self.timekeeper}:{self.date.start}")
