from sqlalchemy import ForeignKey
from sqlalchemy import String, Date, Null
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

import models

Base = declarative_base()


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timekeeper: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[str] = mapped_column(Date)
    end_date: Mapped[str] = mapped_column(Date)
    distance: Mapped[int] = mapped_column(INTEGER(unsigned=True))

    @classmethod
    def from_model(cls, comp: models.Competition) -> "Competition":
        return cls(
            id=comp.id,
            name=comp.name,
            start_date=comp.date.start.replace("/", "-"),
            distance=comp.distance,
        )


class Result(Base):
    __tablename__ = "results"

    # ids
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    runner_id: Mapped[int] = mapped_column(ForeignKey("runners.id"), nullable=False)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False)

    time: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    license: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(20))

    # ranking
    scratch_ranking: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    gender_ranking: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    category_ranking: Mapped[int] = mapped_column(INTEGER(unsigned=True))

    @classmethod
    def from_model(
            cls,
            result: models.Result,
            comp_id: int,
            runner_id: int
    ) -> "Result":
        return cls(
            runner_id=runner_id,
            competition_id=comp_id,
            time=result.time,
            license=result.license if result.license else Null,
            category=result.category,
            scratch_ranking=result.rank.scratch,
            gender_ranking=result.rank.gender,
            category_ranking=result.rank.category,
        )


class Runner(Base):
    __tablename__ = "runners"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_year: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    gender: Mapped[str] = mapped_column(String(1), default="U")

    @classmethod
    def from_model(cls, runner: models.Runner) -> "Runner":
        return cls(
            id=runner.id,
            first_name=runner.first_name,
            last_name=runner.last_name,
            birth_year=runner.birth_year,
            gender=runner.gender.value,
        )
