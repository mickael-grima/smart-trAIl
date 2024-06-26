from datetime import date, timedelta

import pytest

from ...context import database, models
from database.mysql import orm


@pytest.mark.parametrize(
    "competition,expected",
    [
        (
            models.Competition(
                name="c",
                event="e",
                timekeeper="sportpro",
                date=models.Date(start=date(year=2024, month=4, day=10)),
                distance=64,
            ),
            dict(name="c", timekeeper="sportpro"),
        )
    ]
)
def test_Competition(competition: models.Competition, expected: dict):
    res = orm.Competition.from_model(competition)
    assert res == expected


@pytest.mark.parametrize(
    "competition,expected",
    [
        (
            models.Competition(
                name="c",
                event="e",
                timekeeper="sportpro",
                date=models.Date(start=date(year=2024, month=4, day=10)),
                distance=64,
                positive_elevation=1050,
            ),
            dict(
                competition_id=1,
                name="e",
                start_date="2024-04-10",
                distance=64.0,
                positive_elevation=1050,
                negative_elevation=None,
            ),
        )
    ]
)
def test_CompetitionEvent(competition: models.Competition, expected: dict):
    res = orm.CompetitionEvent.from_model(1, competition)
    assert res == expected


@pytest.mark.parametrize(
    "result,expected",
    [
        (
            models.Result(
                runner=models.Runner(
                    first_name="Georges",
                    last_name="POMPIDOU",
                    birth_year=1992,
                    gender=models.Gender.male,
                ),
                time=timedelta(hours=30, minutes=34, seconds=35),
                rank=models.Rank(
                    scratch=23,
                    gender=22,
                    category=13,
                ),
                status=models.ResultStatus.finisher,
                race_number=34234,
                license="LICENCE",
                category="SEH"
            ),
            dict(
                runner_id=2,
                event_id=1,
                status="finisher",
                time="30:34:35",
                license="LICENCE",
                category="SEH",
                scratch_ranking=23,
                gender_ranking=22,
                category_ranking=13,
            )
        ),
        (
            models.Result(
                runner=models.Runner(
                    first_name="Georges",
                    last_name="POMPIDOU",
                    birth_year=1992,
                    gender=models.Gender.male,
                ),
                time=None,
                rank=None,
                status=models.ResultStatus.abandoned,
                race_number=34234,
                license="LICENCE",
                category="SEH"
            ),
            dict(
                runner_id=2,
                event_id=1,
                status="abandoned",
                time=None,
                license="LICENCE",
                category="SEH",
                scratch_ranking=None,
                gender_ranking=None,
                category_ranking=None,
            )
        )
    ]
)
def test_Result(result: models.Result, expected: dict):
    event_id, runner_id = 1, 2
    res = orm.Result.from_model(result, event_id, runner_id)
    assert res == expected


@pytest.mark.parametrize(
    "runner,expected",
    [
        (
            models.Runner(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=1992,
                gender=models.Gender.male,
            ),
            dict(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=1992,
                gender="M",
            )
        ),
        (
            models.Runner(
                first_name="Georges",
                last_name="POMPIDOU",
                gender=models.Gender.male,
            ),
            dict(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=None,
                gender="M",
            )
        ),
        (
            models.Runner(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=1900,
                gender=models.Gender.male,
            ),
            dict(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=None,
                gender="M",
            )
        ),
        (
            models.Runner(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=3000,
                gender=models.Gender.male,
            ),
            dict(
                first_name="Georges",
                last_name="POMPIDOU",
                birth_year=None,
                gender="M",
            )
        ),
    ]
)
def test_Runner(runner: models.Runner, expected: dict):
    res = orm.Runner.from_model(runner)
    assert res == expected
