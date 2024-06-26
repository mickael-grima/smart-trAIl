import re

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
    :param s: string to convert to float
    """
    return float(s.replace(",", "."))


def to_int(s: str):
    return int(s.replace(".", ""))


def convert_distance(d: str) -> float:
    match d.lower():
        case "semi marathon":
            return semi_marathon_dist
        case "marathon":
            return marathon_dist
        case _:
            return to_float(d)


def parse_distance_and_elevation(
        dist: str,
        positive_elevation: str,
        negative_elevation: str
) -> list[list[float, int | None, int | None, int | None]]:
    """
    The website provides us often with several distance and elevations
    Sometimes it says what elevation for what distance, and gives also the year
    This function should be able to extract all tuples
    (distance, positive_elevation, negative_elevation, year) and return it
    """
    # special case - skip
    if dist.lower().startswith("boucle de"):
        return []

    # Extract data from the strings
    distances = dist_creg.findall(dist)  # (distance, year) matches
    pos_elevations = elevation_creg.findall(positive_elevation)  # (elevation, distance) matches
    neg_elevations = elevation_creg.findall(negative_elevation)  # (elevation, distance) matches

    results = [
        [convert_distance(d), None, None, int(year) if year else None]
        for d, year in distances
    ]

    # stop if no results
    if not results:
        return []

    # if only the last tuple has a year, then it applies for all
    last_year = results[-1][-1]
    if last_year is not None and all([r[-1] is None for r in results[:-1]]):
        for r in results[:-1]:
            r[-1] = last_year

    # add elevations
    def add_elevation(elevations: list[tuple[str, str, str]], index: int):
        """
        :param elevations: list of (elevation, corresponding distance, year)
        :param index: index where to add elevation in results (positive or negative elevation)
        """
        # add positive elevation
        if len(elevations) == len(results):  # each distance has an elevation
            for i, (el, _, _) in enumerate(elevations):
                results[i][index] = to_int(el)
        elif len(elevations) == 1:
            el, d, year = elevations[0]
            if not d and not year:  # applies to all distances
                for r in results:
                    r[index] = to_int(el)
            elif d:  # only one distance has an elevation
                for r in results:
                    if r[0] == to_float(d):
                        r[index] = to_int(el)
                        break
            elif year:
                for r in results:
                    if r[-1] == to_int(year):
                        r[index] = to_int(el)
                        break
        else:  # only the first distances have an elevation
            i = 0
            while i < min(len(elevations), len(results)):
                results[i][index] = to_float(elevations[i][0])
                i += 1

    add_elevation(pos_elevations, 1)
    add_elevation(neg_elevations, 2)

    return results
