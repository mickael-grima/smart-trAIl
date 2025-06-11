import re
from typing import TypeVar

marathon_dist = 42.195
semi_marathon_dist = 21.1

dist_creg = re.compile(
    r"(?:^|\D)"
    r"(?P<distance>\d{1,3}(?:[,.]\d+)?|(?:Semi\s+)?Marathon)(?:\s*kms?)?"
    r"(?! heures|[0-9)\n]|x|\s*m)+?"
    r"(?:\s+en (?P<year>\d{4}))?")  # group year

elevation_creg = re.compile(
    r"(?:^|[^0-9,]+)"
    r"(?P<elevation>\d+(?:\.\d+)?)(?!\s*km|,?\d+)(?:\s*m)?"
    r"(?:\s*pour\D+(?P<distance>\d{1,3}(?:[,.]\d+)?)(?:\s*kms?)?)?"
    r"(?:\s+en\s+(?P<year>\d{4}))?"
)


def to_float(s: str) -> float:
    """
    Convert a string to a float.

    Parameters
    ----------
    s: str
        string to convert to float

    Returns
    -------
    float
        The float that has been converted from a string.
    """
    return float(s.replace(",", "."))


def to_int(s: str) -> int:
    """
    Convert a string to an int.

    Parameters
    ----------
    s: str
        string to convert to an int

    Returns
    -------
    int
        The int that has been converted from a string.
    """
    return int(s.replace(".", ""))


def convert_distance(d: str) -> float:
    """Convert some distance strings to a float."""
    match d.lower():
        case "semi marathon":
            return semi_marathon_dist
        case "marathon":
            return marathon_dist
        case _:
            return to_float(d)


ScrappedResultType = TypeVar(
    "ScrappedResultType",
    bound=list[float, int | None, int | None, int | None])


def parse_distance_and_elevation(
        dist: str,
        positive_elevation: str,
        negative_elevation: str
) -> list[ScrappedResultType]:
    """
    Parse distance and elevation from a couple of metadata.

    The website provides often several distances and elevations, wrapped in
    a string. Sometimes it describes an elevation per distance and per year.

    This function should be able to extract all
    (distance, positive_elevation, negative_elevation, year) combinations
    and return it.

    Parameters
    ----------
    dist: str
        All distances in a single string.
    positive_elevation: str
        All positive elevations in a single string.
    negative_elevation: str
        All negative elevations in a single string.

    Returns
    -------
    list[list[float, int | None, int | None, int | None]]
        All possible combinations (distance, positive_elevation,
        negative_elevation, year) as a list.
    """
    # special case - skip
    if dist.lower().startswith("boucle de"):
        return []

    # Extract data from the strings
    # (distance, year) matches
    distances = dist_creg.findall(dist)
    # (elevation, distance) matches
    pos_elevations = elevation_creg.findall(positive_elevation)
    # (elevation, distance) matches
    neg_elevations = elevation_creg.findall(negative_elevation)

    results: list[ScrappedResultType] = [
        [convert_distance(d), None, None, int(year) if year else None]
        for d, year in distances
    ]

    # stop if no results
    if not results:
        return []

    # if only the last tuple has a year, then it applies for all
    last_year = results[-1][-1]
    if last_year is not None and all(r[-1] is None for r in results[:-1]):
        for r in results[:-1]:
            r[-1] = last_year

    # add elevations
    __add_missing_elevations(results, pos_elevations, 1)
    __add_missing_elevations(results, neg_elevations, 2)

    return results


def __add_missing_elevations(
        results: list[ScrappedResultType],
        elevations: list[tuple[str, str, str]],
        index: int
) -> None:
    """
    Add missing elevation to all provided elevations.

    Parameters
    ----------
    elevations: list[tuple[str, str, str]]
        list of (elevation, corresponding distance, year) as strings.
    index: int
        index where to add elevation in results (positive or negative
        elevation).
    """
    # each distance has an elevation
    if len(elevations) == len(results):
        for i, (elevation, _, _) in enumerate(elevations):
            results[i][index] = to_int(elevation)

    # There is a single elevation for all results
    elif len(elevations) == 1:
        elevation, distance, year = elevations[0]
        elevation = to_int(elevation)
        distance = to_float(distance) if distance else None
        year = to_int(year) if year else None
        __add_missing_elevations_from_a_single_source(
            results, elevation, distance, year, index)

    # only the first distances have an elevation
    else:
        i = 0
        while i < min(len(elevations), len(results)):
            results[i][index] = to_float(elevations[i][0])
            i += 1


def __add_missing_elevations_from_a_single_source(
        results: list[ScrappedResultType],
        elevation: int,
        distance: float | None,
        year: int | None,
        index: int
) -> None:
    """
    Add unique missing elevation to all results.

    If distance is provided, only add elevation to the first result whose
    distance corresponds to distance.

    Otherwise, if the year is provided, only add elevation to the first result
    whose year corresponds to year.

    Otherwise, add elevation to all results.

    Parameters
    ----------
    results: list[ScrappedResultType]
        list of scrapped results from the html table.
    elevation: int
        The elevation to add.
    distance: float
        The competition distance.
    year: int
        The competition year.
    index: int
        index where to add elevation in results (positive or negative
        elevation).
    """
    if distance:  # only one distance has an elevation
        for result in results:
            if result[0] == distance:
                result[index] = elevation
                return
    if year:
        for result in results:
            if result[-1] == year:
                result[index] = elevation
                return
    for result in results:
        result[index] = elevation
