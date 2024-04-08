from datetime import time, date

from sqlalchemy import ForeignKey, UniqueConstraint, String, Date, Time
from sqlalchemy.dialects.mysql import SMALLINT, CHAR, INTEGER, YEAR
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

import models

Base = declarative_base()


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timekeeper: Mapped[str] = mapped_column(String(50), nullable=False)

    # competition should be unique with name, timekeeper
    __table_args__ = (UniqueConstraint("name", "timekeeper",),)

    @classmethod
    def from_model(cls, comp: models.Competition) -> dict:
        return dict(
            name=comp.name,
            timekeeper=comp.timekeeper,
        )


class CompetitionEvent(Base):
    __tablename__ = "competitionEvents"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    distance: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False)

    # competition should be unique with name, timekeeper and start_date
    __table_args__ = (UniqueConstraint("name", "start_date", "distance"),)

    @classmethod
    def from_model(cls, competition_id: int, comp: models.Competition) -> dict:
        return dict(
            name=comp.event,
            start_date=comp.date.start.strftime("%Y-%m-%d"),
            distance=comp.distance,
            competition_id=competition_id
        )


class Result(Base):
    __tablename__ = "results"

    # ids
    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    runner_id: Mapped[int] = mapped_column(ForeignKey("runners.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("competitionEvents.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=True)
    license: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(20), nullable=True)

    # ranking
    scratch_ranking: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=True)
    gender_ranking: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=True)
    category_ranking: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=True)

    @classmethod
    def from_model(
            cls,
            result: models.Result,
            event_id: int,
            runner_id: int
    ) -> dict:
        return dict(
            runner_id=runner_id,
            event_id=event_id,
            status=result.status.value,
            time=result.time.strftime("%H:%M:%S") if result.time else None,
            license=result.license if result.license else None,
            category=result.category,
            scratch_ranking=result.rank.scratch if result.rank else None,
            gender_ranking=result.rank.gender if result.rank else None,
            category_ranking=result.rank.category if result.rank else None,
        )


class Runner(Base):
    __tablename__ = "runners"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_year: Mapped[int] = mapped_column(YEAR, nullable=True)
    gender: Mapped[str] = mapped_column(CHAR(1), default="U", nullable=False)

    __table_args__ = (UniqueConstraint("first_name", "last_name", "birth_year"),)

    @classmethod
    def from_model(cls, runner: models.Runner) -> dict:
        return dict(
            first_name=runner.first_name,
            last_name=runner.last_name,
            birth_year=runner.birth_year,
            gender=runner.gender.value,
        )