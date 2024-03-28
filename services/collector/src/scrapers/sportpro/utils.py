import re

import models

dst_regex = re.compile(r"(?P<dist>[0-9]+(\.[0-9]*)?)(\s*km)?")
time_regex = re.compile(r"((?P<hours>[0-9]+):)?(?P<minutes>[0-5][0-9]):(?P<seconds>[0-5][0-9])")


def parse_distance(text: str) -> float:
    """
    Parse a text distance to a float
    
    Ex: 0.1 km -> 0.1
    """
    match = dst_regex.match(text)
    if match is not None:
        return float(match.groupdict()["dist"])
    return -1


def parse_time(text: str) -> int:
    """
    Parse the time as text and convert it to a total of seconds
    Example:
      01:43:51 -> 6231
    """
    match = time_regex.match(text)
    if match is not None:
        groups = match.groupdict()
        hours = int(groups.get("hours", "0"))
        minutes = int(groups["minutes"])
        seconds = int(groups["seconds"])
        return 3600 * hours + 60 * minutes + seconds
    return -1


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
