import pytest

from ...context import scrapers
from scrapers.runraid import parser


def test_parse_date():
    pass


@pytest.mark.parametrize(
    "dist,pos,neg,expected",
    [
        (
            "20 km (équipe de 8)",
            "",
            "",
            [[20, None, None, None],]
        ),
        (
            "4, 12 et 17km",
            "",
            "",
            [
                [4, None, None, None],
                [12, None, None, None],
                [17, None, None, None]
            ]
        ),
        (
            "25 km en 2024",
            "400 m",
            "400 m",
            [[25, 400, 400, 2024]]
        ),
        (
            "42 km",
            "",
            "",
            [[42, None, None, None]]
        ),
        (
            "40 et 66 km en 2024",
            "2550 m",
            "2550 m",
            [
                [40, 2550, 2550, 2024],
                [66, 2550, 2550, 2024],
            ]
        ),
        (
            "8km (rando) et 23 km",
            "",
            "",
            [
                [8, None, None, None],
                [23, None, None, None]
            ]
        ),
        (
            "15 et 40 km (solo ou relaisx2)",
            "100 et 1600m pour le 40km",
            "",
            [
                [15, 100, None, None],
                [40, 1600, None, None],
            ]
        ),
        (
            "11 et 22 km",
            "",
            "",
            [
                [11, None, None, None],
                [22, None, None, None],
            ]
        ),
        (
            "10, 18 et 35km en 2023",
            "",
            "",
            [
                [10, None, None, 2023],
                [18, None, None, 2023],
                [35, None, None, 2023],
            ]
        ),
        (
            "1, 2 ou 4.7 km",
            "",
            "",
            [
                [1, None, None, None],
                [2, None, None, None],
                [4.7, None, None, None],
            ]
        ),
        (
            "42,195 et 21 kms",
            "",
            "",
            [
                [42.195, None, None, None],
                [21, None, None, None],
            ]
        ),
        (
            "2,5 km et 9,7km",
            "",
            "",
            [
                [2.5, None, None, None],
                [9.7, None, None, None],
            ]
        ),
        (
            "173 km en 2021, 149 km en 2024",
            "8000 m en 2024",
            "8000 m",
            [
                [173, None, 8000, 2021],
                [149, 8000, 8000, 2024],
            ]
        ),
        (
            "10x10x 400m sur piste",
            "",
            "",
            []
        ),
        (  # too complicated - skip for now
            "Boucle de 6km - 33 heures - 198 km",
            "165 m de D+ par boucle",
            "",
            []
        ),
        (
            "10 km et Semi Marathon",
            "",
            "",
            [
                [10, None, None, None],
                [21.1, None, None, None],
            ]
        ),
        (
            "10 km et Marathon en 2024",
            "",
            "",
            [
                [10, None, None, 2024],
                [42.195, None, None, 2024],
            ]
        ),
        (
            "164 (solo ou relais x 6), 117, 72, 43 km",
            "9500 m pour le 164km",
            "",
            [
                [164, 9500, None, None],
                [117, None, None, None],
                [72, None, None, None],
                [43, None, None, None],
            ]
        ),
        (
            "130 (solo, duo, relais), 70, 35, 10 et 5",
            "5000, 2400 ou 970 m",
            "",
            [
                [130, 5000, None, None],
                [70, 2400, None, None],
                [35, 970, None, None],
                [10, None, None, None],
                [5, None, None, None],
            ]
        ),
    ]
)
def test_parse_distance_and_elevation(
        dist: str,
        pos: str,
        neg: str,
        expected: list[tuple[float, float | None, float | None]]
):
    res = parser.parse_distance_and_elevation(dist, pos, neg)
    assert res == expected
