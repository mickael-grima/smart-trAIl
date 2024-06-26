import datetime
import logging
from datetime import date, timedelta

from sqlalchemy import ForeignKey, UniqueConstraint, String, Date, Time, PrimaryKeyConstraint
from sqlalchemy.dialects.mysql import SMALLINT, CHAR, INTEGER, YEAR, DECIMAL
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

import models
from . import utils

logger = logging.getLogger(__name__)

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
    __tablename__ = "competition_events"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    distance: Mapped[float] = mapped_column(DECIMAL(4, 1), nullable=False)
    positive_elevation: Mapped[int] = mapped_column(SMALLINT, nullable=True)
    negative_elevation: Mapped[int] = mapped_column(SMALLINT, nullable=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False)

    # competition should be unique with name, timekeeper and start_date
    __table_args__ = (
        UniqueConstraint("name", "start_date", "distance"),
    )

    @classmethod
    def from_model(cls, competition_id: int, comp: models.Competition) -> dict:
        return dict(
            name=comp.event,
            start_date=comp.date.start.strftime("%Y-%m-%d"),
            distance=comp.distance,
            positive_elevation=comp.positive_elevation,
            negative_elevation=comp.negative_elevation,
            competition_id=competition_id,
        )


class Result(Base):
    __tablename__ = "results"

    # ids
    runner_id: Mapped[int] = mapped_column(ForeignKey("runners.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("competition_events.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    time: Mapped[timedelta] = mapped_column(Time, nullable=True)
    license: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(20), nullable=True)

    # ranking
    scratch_ranking: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=True)
    gender_ranking: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=True)
    category_ranking: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('runner_id', 'event_id', name="runner-event-pk"),
    )

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
            time=utils.format_timedelta(result.time) if result.time else None,
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

    __table_args__ = (
        UniqueConstraint("first_name", "last_name", "birth_year"),
    )

    @classmethod
    def from_model(cls, runner: models.Runner) -> dict:
        current_year = datetime.datetime.now().year
        birth_year = runner.birth_year
        # year before 1901 are not accepted (and not relevant anyway)
        if birth_year is not None and  not 1901 <= birth_year <= current_year:
            logger.warning(
                f"not valid BirthYear={birth_year} for "
                f"runner=\"{runner.first_name} {runner.last_name}\"")
            birth_year = None
        return dict(
            first_name=runner.first_name,
            last_name=runner.last_name,
            birth_year=birth_year,
            gender=runner.gender.value,
        )
