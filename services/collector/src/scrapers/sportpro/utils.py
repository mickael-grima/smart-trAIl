import re
from datetime import date, datetime, timedelta
from typing import Callable, TypeVar

import models

dst_regex = re.compile(r"^(?P<dist>[0-9]+(\.[0-9]*)?)(\s*km)?$")
time_regex = re.compile(r"^((?P<hours>[0-9]+):)?(?P<minutes>[0-5][0-9]):(?P<seconds>[0-5][0-9])$")


def parse_distance(text: str) -> float:
    """
    Parse a text distance to a float
    
    Ex: 0.1 km -> 0.1
    """
    match = dst_regex.match(text)
    if match is not None:
        return float(match.groupdict()["dist"])
    return -1


def parse_time(text: str) -> timedelta | None:
    """
    Parse the time as text and convert it to a total of seconds
    Example:
      01:43:51 -> 6231
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
    return datetime.strptime(text, "%d/%m/%Y").date()


def get_gender(text: str) -> models.Gender:
    match text.upper():
        case "M":
            return models.Gender.male
        case "F":
            return models.Gender.female
        case _:
            return models.Gender.undefined


def complete_url(host: str, url: str) -> str:
    """
    add host and initial / in case the url is incomplete
    """
    if url.startswith("http"):
        return url
    elif url.startswith("/"):
        return host + url
    else:
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
    """
    cast `value` to type `D` using func
    If it fails, return default
    """
    try:
        return func(value)
    except:
        return default
