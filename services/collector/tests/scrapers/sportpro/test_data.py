from datetime import date, timedelta
from typing import Optional

import pytest

from collector import models
from collector.scrapers.sportpro import data


def test_Row():
    """
    Test inherited method `is_valid`: True by default
    """
    class MyRow(data.Row):
        @classmethod
        def from_dict(cls, row: dict[str, str]) -> Optional["MyRow"]:
            return None

    assert MyRow().is_valid() is True


@pytest.mark.parametrize(
    "row,is_valid,model",
    [
        (
            {
                "Date": "07/04/2024",
                "Compétition": "Championnat 10km Ste Suzanne",
                "Épreuve": "10km Ste Suzanne Open",
                "Distance": "10 km",
                "Ville": "Sainte-Suzanne",
                "Résultats": "resultats/epreuve/06081-10km-ste-suzanne-open/",
            },
            True,
            models.Competition(
                name="Championnat 10km Ste Suzanne",
                event="10km Ste Suzanne Open",
                timekeeper="sportpro",
                date=models.Date(start=date(year=2024, month=4, day=7)),
                distance=10.,
            ),
        ),
        (
            {
                "Date": "24/03/2024",
                "Compétition": "Juniors Trail Colorado",
                "Épreuve": "Relais Minimes/Cadets/Juniors",
                "Distance": "0.1 km",
                "Ville": "La Montagne",
            },
            False,
            models.Competition(
                name="Juniors Trail Colorado",
                event="Relais Minimes/Cadets/Juniors",
                timekeeper="sportpro",
                date=models.Date(start=date(year=2024, month=3, day=24)),
                distance=0.1,
            ),
        ),
    ]
)
def test_CompetitionRow(
        row: dict[str, str],
        is_valid: bool,
        model: models.Competition
):
    r = data.CompetitionRow.from_dict(row)
    assert r.is_valid() == is_valid
    m = r.to_model()
    assert m == model


@pytest.mark.parametrize(
    "row,is_valid,model",
    [
        (
            {
                "Scratch": "1",
                "Temps": "00:35:01",
                "Nom": "NOEL",
                "Prénom": "Fabrice",
                "Sexe": "M",
                "Né(e)": "1975",
                "Cat.": "M2H",
                "Licence": "",
                "Team": "",
                "Clst sexe": "1",
                "Clst cat.": "1",
                "Dossard": "61886",
            },
            True,
            models.Result(
                runner=models.Runner(
                    first_name="Fabrice",
                    last_name="NOEL",
                    birth_year=1975,
                    gender=models.Gender.male,
                ),
                time=timedelta(minutes=35, seconds=1),
                rank=models.Rank(
                    scratch=1,
                    gender=1,
                    category=1,
                ),
                status=models.ResultStatus.finisher,
                race_number=61886,
                license="",
                category="M2H",
            )
        ),
        (
            {
                "Scratch": "1",
                "Temps": "00:35:01",
                "Nom": "NOEL",
                "Prénom": "Fabrice",
                "Sexe": "M",
                "Né(e)": "",
                "Cat.": "M2H",
                "Licence": "",
                "Team": "",
                "Clst sexe": "1",
                "Clst cat.": "1",
                "Dossard": "61886",
            },
            False,
            models.Result(
                runner=models.Runner(
                    first_name="Fabrice",
                    last_name="NOEL",
                    gender=models.Gender.male,
                ),
                time=timedelta(hours=0, minutes=35, seconds=1),
                rank=models.Rank(
                    scratch=1,
                    gender=1,
                    category=1,
                ),
                status=models.ResultStatus.finisher,
                race_number=61886,
                license="",
                category="M2H",
            )
        ),
        (
            {
                "": "Non partant",
                "Nom": "MICALLEF",
                "Prénom": "NICOLAS",
                "Sexe": "M",
                "Né(e)": "1991",
                "Cat.": "SEH",
                "Licence": "",
                "Team": "",
                "Dossard": "61804"
            },
            True,
            models.Result(
                runner=models.Runner(
                    first_name="NICOLAS",
                    last_name="MICALLEF",
                    birth_year=1991,
                    gender=models.Gender.male,
                ),
                status=models.ResultStatus.non_starter,
                race_number=61804,
                license="",
                category="SEH",
            )
        ),
        (
            {
                "": "Abandon",
                "Nom": "MICALLEF",
                "Prénom": "NICOLAS",
                "Sexe": "M",
                "Né(e)": "1991",
                "Cat.": "SEH",
                "Licence": "",
                "Team": "",
                "Dossard": "61804"
            },
            True,
            models.Result(
                runner=models.Runner(
                    first_name="NICOLAS",
                    last_name="MICALLEF",
                    birth_year=1991,
                    gender=models.Gender.male,
                ),
                status=models.ResultStatus.abandoned,
                race_number=61804,
                license="",
                category="SEH",
            )
        ),
        (
            {
                "": "Disqualification",
                "Nom": "MICALLEF",
                "Prénom": "NICOLAS",
                "Sexe": "M",
                "Né(e)": "1991",
                "Cat.": "SEH",
                "Licence": "",
                "Team": "",
                "Dossard": "61804"
            },
            True,
            models.Result(
                runner=models.Runner(
                    first_name="NICOLAS",
                    last_name="MICALLEF",
                    birth_year=1991,
                    gender=models.Gender.male,
                ),
                status=models.ResultStatus.disqualified,
                race_number=61804,
                license="",
                category="SEH",
            )
        ),
        (
            {
                "": "",
                "Nom": "MICALLEF",
                "Prénom": "NICOLAS",
                "Sexe": "M",
                "Né(e)": "1991",
                "Cat.": "SEH",
                "Licence": "",
                "Team": "",
                "Dossard": "61804"
            },
            True,
            models.Result(
                runner=models.Runner(
                    first_name="NICOLAS",
                    last_name="MICALLEF",
                    birth_year=1991,
                    gender=models.Gender.male,
                ),
                status=models.ResultStatus.unknown,
                race_number=61804,
                license="",
                category="SEH",
            )
        ),
        (
            {
                "": "whatever",
                "Nom": "MICALLEF",
                "Prénom": "NICOLAS",
                "Sexe": "M",
                "Né(e)": "1991",
                "Cat.": "SEH",
                "Licence": "",
                "Team": "",
                "Dossard": "61804"
            },
            True,
            models.Result(
                runner=models.Runner(
                    first_name="NICOLAS",
                    last_name="MICALLEF",
                    birth_year=1991,
                    gender=models.Gender.male,
                ),
                status=models.ResultStatus.unknown,
                race_number=61804,
                license="",
                category="SEH",
            )
        ),
        (
            {},
            True,
            None
        ),
    ]
)
def test_ResultRow(
        row: dict[str, str],
        is_valid: bool,
        model: models.Result | None,
):
    r = data.ResultRow.from_dict(row)
    if model is None:
        assert r is None
    else:
        assert r.is_valid() == is_valid
        m = r.to_model()
        assert m == model
