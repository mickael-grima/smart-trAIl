from datetime import timedelta

import pytest

from ...context import database
from database.mysql import utils


@pytest.mark.parametrize(
    "td,expected",
    [
        (timedelta(seconds=34), "00:00:34"),
        (timedelta(seconds=4), "00:00:04"),
        (timedelta(minutes=35, seconds=34), "00:35:34"),
        (timedelta(minutes=3), "00:03:00"),
        (timedelta(hours=12, seconds=34), "12:00:34"),
        (timedelta(hours=2, minutes=34), "02:34:00"),
        (timedelta(hours=987, minutes=34, seconds=12), "987:34:12"),
    ]
)
def test_format_timedelta(td: timedelta, expected: str):
    res = utils.format_timedelta(td)
    assert res == expected
