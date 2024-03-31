import enum
import hashlib
from typing import Any

import pydantic


class Gender(enum.Enum):
    male = "M"
    female = "F"
    undefined = "U"


class Date(pydantic.BaseModel):
    start: str = ...
    end: str | None = None


class Rank(pydantic.BaseModel):
    scratch: int = ...
    gender: int = ...
    category: int = ...


class IdModel(pydantic.BaseModel):
    id: int = ...

    def __hash__(self):
        return self.id


class Runner(IdModel):
    first_name: str = ...
    last_name: str = ...
    birth_year: int = ...
    gender: Gender = ...

    @pydantic.model_validator(mode='before')
    @classmethod
    def set_id(cls, data: Any):
        text = f"{data['first_name']}:{data['last_name']}:{data['birth_year']}"
        hash_object = hashlib.sha1(text.lower().encode())
        return hash_object.hexdigest()


class Result(pydantic.BaseModel):
    runner: Runner = ...
    time: int = ...
    rank: Rank = ...
    race_number: int = ...
    license: str | None = None
    category: str = ...


class Competition(IdModel):
    name: str = ...
    timekeeper: str = ...
    date: Date = ...
    distance: float = ...
    results: list[Result] = pydantic.Field(default_factory=list)

    @pydantic.model_validator(mode='before')
    @classmethod
    def set_id(cls, data: Any):
        text = f"{data['name']}:{data['timekeeper']}:{data['date']['start']}"
        hash_object = hashlib.sha1(text.lower().encode())
        return hash_object.hexdigest()
