from datetime import date

import pytest

from ...context import scrapers
from scrapers.runraid import utils


@pytest.mark.parametrize(
    "text,expected",
    [
        ("08-04-2024", date(year=2024, month=4, day=8)),
        ("8-4-2024", date(year=2024, month=4, day=8)),
    ]
)
def test_parse_date(text: str, expected: date):
    d = utils.parse_date(text)
    assert d == expected, f"Unexpected result={d}, when {expected} was expected"