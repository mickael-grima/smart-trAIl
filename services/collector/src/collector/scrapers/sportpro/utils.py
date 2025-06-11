import re
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import TypeVar

dst_regex = re.compile(r"^(?P<dist>[0-9]+(\.[0-9]*)?)(\s*km)?$")
time_regex = re.compile(
    r"^((?P<hours>[0-9]+):)?(?P<minutes>[0-5][0-9]):(?P<seconds>[0-5][0-9])$")


def parse_distance(text: str) -> float:
    """
    Parse a text distance as a float.

    Examples
    --------
    parse_distance("0.1 km")
    >> 0.1
    """
    match = dst_regex.match(text)
    if match is not None:
        return float(match.groupdict()["dist"])
    return -1


def parse_time(text: str) -> timedelta | None:
    """
    Parse the time as text and convert it to a total of seconds.

    Examples
    --------
    parse_time("01:43:51")
    >> timedelta(seconds=6231)
    """
    match = time_regex.match(text)
    if match is not None:
        groups = match.groupdict()
        hours = int(groups.get("hours") or "0")
        minutes = int(groups["minutes"])
        seconds = int(groups["seconds"])
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return None


def parse_date(text: str) -> date:
    """
    Parse date from text.

    Examples
    --------
    parse_date("8/6/2025")
    >> date(year=2025, month=6, date=8)
    """
    return datetime.strptime(text, "%d/%m/%Y").date()  # noqa: DTZ007


def complete_url(host: str, url: str) -> str:
    """Add host and initial / in case the url is incomplete."""
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return host + url
    return f"{host}/{url}"


# Generic returned value after casting
T = TypeVar('T')
# default returned value
D = TypeVar('D')


def cast_or_default(
        value: str,
        func: Callable[[str], T],
        default: D | None = None
) -> T | D | None:
    """Cast `value` to type `D` using func. If it fails, return default."""
    try:
        return func(value)
    except Exception:  # noqa: BLE001
        return default
