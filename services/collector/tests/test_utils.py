from datetime import datetime, date

import pytest

from collector import utils


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        (
            "Trail de l'Eden",
            "Trail de l'Eden",
            1.0,
        ),
        (
            "Trail de l'Eden",
            "Trail de l'Eden en relais",
            1.0,
        ),
        (
            "Trail de l'Eden en relais",
            "Trail de l'Eden",
            1.0,
        ),
        (
            "Tangue",
            "Course Tangue 2024",
            1.0,
        ),
        (
            "D-Tour 45 et 70 km",
            "D'Tour 45",
            0.889,
        ),
        (
            "D-Tour 45 et 70 km",
            "Le D'TOUR",
            0.667,
        ),
        (
            "Trail de la Griffe du Diable",
            "Trail Griffe du Diable Piton de la Fournaise Jacob",
            0.88,
        ),
        (
            "Cross du Piton des Neiges",
            "Cross du Vétyver",
            0.714,
        ),
        (
            "Cross du Piton des Neiges",
            "Championnat Cross de la Plaine des Palmistes",
            0.704,
        ),
        (
            "Cross du Piton des Neiges",
            "Cross du Bassin Bleu",
            0.684,
        ),
        (
            "Boucle du Piton des Neiges",
            "La boucle du Piton de Neiges",
            0.980,
        ),
        (
            "Trail de Grand Bassin Mollaret",
            "Trail Grand Bassin",
            1.0,
        ),
    ]
)
def test_string_similarity(s1: str, s2: str, expected: float):
    sim = utils.sentence_similarity(s1, s2)
    assert abs(sim - expected) < 10e-3, \
        f"Unexpected {sim:.3f}, when {expected:.3f} was expected. \n\"{s1}\" to \"{s2}\""


@pytest.mark.parametrize(
    "d1,d2,perc90_delta,expected",
    [
        (43, 45, 2, 0.9),
        (40, 45, 2, 0.518),
        (42, 45, 2, 0.789),
        (45, 45, 2, 1),
        (43, 40, 3, 0.9),
        (None, 40, 3, 1.0),
        (43, None, 3, 1.0),
    ]
)
def test_general_distance_similarity(d1: float, d2: float, perc90_delta: float, expected: float):
    sim = utils.distance_similarity(d1, d2, perc90_delta=perc90_delta)
    assert abs(sim - expected) < 10e-3, \
        f"Unexpected {sim:.3f}, when {expected:.3f} was expected. \n\"{d1}\" to \"{d2}\""


@pytest.mark.parametrize(
    "d1,d2,expected",
    [
        (
            datetime.strptime("01-07-2024", "%d-%m-%Y").date(),
            datetime.strptime("01-07-2024", "%d-%m-%Y").date(),
            0,
        ),
        (
            datetime.strptime("01-07-2024", "%d-%m-%Y").date(),
            datetime.strptime("02-07-2024", "%d-%m-%Y").date(),
            24,
        ),
        (
            datetime.strptime("02-07-2024", "%d-%m-%Y").date(),
            datetime.strptime("01-07-2024", "%d-%m-%Y").date(),
            -24,
        ),
    ]
)
def test_hours_diff(d1: date, d2: date, expected: int):
    hours = utils.hours_diff(d1, d2)
    assert hours == expected, f"Unexpected {hours} hours, when {expected} hours was expected"
