from datetime import timedelta, date
from typing import Optional, Callable, Any

import pytest

from collector.scrapers.sportpro import utils


@pytest.mark.parametrize(
    "text,expected",
    [
        ("0.1 km", 0.1),
        ("63 km", 63),
        ("63km", 63),
        ("63 m", -1),
        ("63", 63),
    ]
)
def test_parse_distance(text: str, expected: float):
    dist = utils.parse_distance(text)
    assert dist == expected, f"Unexpected result={dist}, when {expected} was expected"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("01:45:34", timedelta(hours=1, minutes=45, seconds=34)),
        ("45:34", timedelta(hours=0, minutes=45, seconds=34)),
        ("32:45:34", timedelta(hours=32, minutes=45, seconds=34)),
        ("ad:34", None),
    ]
)
def test_parse_time(text: str, expected: Optional[timedelta]):
    t = utils.parse_time(text)
    assert t == expected, f"Unexpected result={t}, when {expected} was expected"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("8/4/2024", date(year=2024, month=4, day=8)),
        ("08/04/2024", date(year=2024, month=4, day=8)),
    ]
)
def test_parse_date(text: str, expected: date):
    d = utils.parse_date(text)
    assert d == expected, f"Unexpected result={d}, when {expected} was expected"


@pytest.mark.parametrize(
    "partial_url,expected",
    [
        ("https://test.com/path?q=test", "https://test.com/path?q=test"),
        ("/path?q=test", "http://example.com/path?q=test"),
        ("path?q=test", "http://example.com/path?q=test"),
    ]
)
def test_complete_url(partial_url: str, expected: str):
    host = "http://example.com"
    url = utils.complete_url(host, partial_url)
    assert url == expected, f"Unexpected result={url}, when {expected} was expected"


@pytest.mark.parametrize(
    "text,func,default,expected",
    [
        ("12", int, None, 12),
        ("unknown", int, None, None),
        ("unknown", int, 0, 0),
        ("123.4", float, None, 123.4),
    ]
)
def test_cast_or_default(text: str, func: Callable[[str], Any], default: Any, expected: Any):
    casted = utils.cast_or_default(text, func, default)
    assert casted == expected, f"Unexpected result={casted}, when {expected} was expected"
