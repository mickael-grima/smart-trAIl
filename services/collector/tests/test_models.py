from datetime import datetime

import pytest

from . context import models


competitions: dict[int, models.Competition] = {
    111: models.Competition(
        event="Trail de l'Eden",
        name="Trail de l'Eden",
        timekeeper="sportpro",
        date=models.Date(start=datetime.strptime("01-07-2024", "%d-%m-%Y").date()),
        distance=23,
        positive_elevation=900,
    ),
    112: models.Competition(
        event="Trail des griffes du diable",
        name="Trail Volcan",
        timekeeper="sportpro",
        date=models.Date(start=datetime.strptime("04-05-2024", "%d-%m-%Y").date()),
        distance=15,
    ),
    113: models.Competition(
        event="course autour du lac",
        name="organisateur",
        timekeeper="sportpro",
        date=models.Date(start=datetime.strptime("01-07-2024", "%d-%m-%Y").date()),
        distance=23,
    ),
}


@pytest.mark.parametrize(
    "metadata,expected",
    [
        (
            models.CompetitionMetaData(
                event="Trail de l'Eden en relais",
                date=models.Date(start=datetime.strptime("01-07-2024", "%d-%m-%Y").date()),
                distance=23,
                positive_elevation=900,
            ),
            111
        ),
        (
            models.CompetitionMetaData(
                event="Trail des sources",
                date=models.Date(start=datetime.strptime("11-09-2024", "%d-%m-%Y").date()),
                distance=31,
                positive_elevation=1500,
            ),
            None
        ),
        (
            models.CompetitionMetaData(
                event="Trail des griffe du diable",
                date=models.Date(start=datetime.strptime("04-05-2024", "%d-%m-%Y").date()),
                distance=15.3,
                positive_elevation=500,
            ),
            112
        ),
    ]
)
def test_CompetitionMetaData_find_best_match(
        metadata: models.CompetitionMetaData,
        expected: models.CompetitionMetaData,
):
    """
    Find best match for `metadata` in `competitions`
    """
    comp_id = metadata.find_best_match(competitions)
    assert comp_id == expected, \
        f"Unexpected competition id={comp_id}, {expected} was expected instead"
