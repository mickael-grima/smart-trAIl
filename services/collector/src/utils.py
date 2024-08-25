import datetime
import math

import Levenshtein

__all__ = ["string_similarity"]


def accept_none(return_sim: float = 1.0):
    """
    Return a decorator that returns the similarity `return_sim` if
    any of the input is None
    """
    def decorator(func):
        def wrapper(o1: any, o2: any, *args, **kwargs):
            if o1 is None or o2 is None:
                return return_sim
            return func(o1, o2, *args, **kwargs)
        return wrapper
    return decorator


@accept_none()
def distance_similarity(d1: float, d2: float, perc90_delta: float = 2):
    """
    :param d1: distance to compare
    :param d2: distance to compare
    :param perc90_delta: what difference between d1 and d2 should give the
      value 0.9
    :return: a score between 0 and 1: 1 means that d1 and d2 are equal. 0 means
    that d2 - d1 = infinite
    """
    coeff = perc90_delta ** 2 / 0.10536  # 2 km difference leads to a score of 0.9
    return math.exp(- (d2 - d1) ** 2 / coeff)


def string_similarity(s1: str, s2: str) -> float:
    """
    Compare s1 to s2
    it has the highest similarity score if any words subset of s1
    matches s2, using the levenshtein distance, and vice-versa.
    """
    s1, s2 = s1.lower(), s2.lower()
    return max(
        string_similarity_rec(s1, s2),
        string_similarity_rec(s2, s1)
    )


def string_similarity_rec(s1: str, s2: str, prefix: str = "") -> float:
    s1 = s1.strip()
    s2 = s2.strip()
    if s1 == "" or s2 == "":
        return 0.

    if " " not in s1:
        return max(Levenshtein.ratio(f"{prefix} {s1}".strip(), s2), Levenshtein.ratio(prefix, s2))

    next_word = s1.split()[0]
    new_prefix = f"{prefix} {next_word}".strip()
    s1 = s1[len(next_word):]
    return max(
        string_similarity_rec(s1, s2, prefix=prefix),
        string_similarity_rec(s1, s2, prefix=new_prefix),
    )


def hours_diff(d1: datetime.date, d2: datetime.date) -> int:
    td = d2 - d1
    return td.days * 24 + td.seconds // 3600
