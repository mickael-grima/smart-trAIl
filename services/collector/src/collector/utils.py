import datetime
import math
from collections.abc import Callable
from typing import TypeVar

import Levenshtein

__all__ = ["sentence_similarity"]

SimArg = TypeVar('SimArg')
SimFuncType = Callable[[SimArg, SimArg, ...], float]


def sim_func_accept_none(
        return_sim: float = 1.0) -> Callable[[SimFuncType], SimFuncType]:
    """
    Make a similarity function accepts None arguments.

    Parameters
    ----------
    return_sim : float
        The default similarity value in case 1 of the arguments is none.

    Returns
    -------
    Return a decorator that returns the similarity `return_sim` if
    any of the input is None.
    """

    def decorator(func: SimFuncType) -> SimFuncType:
        """Decorate the similarity function."""

        def wrapper(o1: SimArg, o2: SimArg, **kwargs) -> float:  # noqa: ANN003
            """Return default similarity value if 1 of the inputs is None."""
            if o1 is None or o2 is None:
                return return_sim
            return func(o1, o2, **kwargs)

        return wrapper
    return decorator


@sim_func_accept_none()
def distance_similarity(d1: float, d2: float, perc90_delta: float = 2) -> float:
    """
    Calculate the distance similarity between two floats.

    We use the euclidian distance, put back to a value between 0 and 1.
    If d1 & d2 are the same, their similarity is 1.0.
    If d1 & d2 are the furthest possible, their similarity is 0.0.

    The function is symmetrical: inverting d1 and d2 will give the same result.

    Parameters
    ----------
    d1: float
        distance to compare.
    d2: float
        distance to compare.
    perc90_delta: float
        what difference between d1 and d2 should give the
        value 0.9.

    Returns
    -------
    float
        A score between 0 and 1: 1 means that d1 and d2 are equal. 0 means
        that d2 - d1 = infinite.
    """
    # 2 km difference leads to a score of 0.9
    coeff = perc90_delta ** 2 / 0.10536
    return math.exp(- (d2 - d1) ** 2 / coeff)


def sentence_similarity(s1: str, s2: str) -> float:
    """
    Compare s1 to s2.

    it has the highest similarity score if any words subset of s1
    matches s2, using the levenshtein distance, and vice-versa.

    The function is symmetrical: inverting s1 and s2 will give the same result.

    Parameters
    ----------
    s1: str
        The first string to compare to the second string.
    s2: str
        The second string to compare to the first string.

    Returns
    -------
    float
    """
    s1, s2 = s1.lower(), s2.lower()
    return max(
        sentence_similarity_rec(s1, s2),
        sentence_similarity_rec(s2, s1)
    )


def sentence_similarity_rec(s1: str, s2: str, prefix: str = "") -> float:
    """
    Calculate the similarity between two sentences.

    The similarity is calculated based on the Levenshtein distance. We evaluate
    all combinations of words of s1 (keeping the order), and calculate its
    distance with s2, and we keep the maximum.

    Parameters
    ----------
    s1: str
        The first sentence to be compared to another sequence. From this
        sentence we extract all possible chain of words to be also compared
        to s2.
    s2: str
        The second sentence to which we compare the first sequence.
    prefix: str
        Remember the previous words in the very first sentence. This makes the
        function recursive.

    Returns
    -------
    float
        A similarity score between 0 and 1.

    Examples
    --------
    sentence_similarity_rec("world", "hello world")
    >> 1

    sentence_similarity_rec("hello", "hello world")
    >> 1

    sentence_similarity_rec("helo", "hello world")
    >> Levenshtein.distance("helo", "hello")
    """
    s1 = s1.strip()
    s2 = s2.strip()
    if s1 == "" or s2 == "":
        return 0.

    if " " not in s1:
        # we have a single word
        return max(
            Levenshtein.ratio(f"{prefix} {s1}".strip(), s2),
            Levenshtein.ratio(prefix, s2)
        )

    next_word = s1.split()[0]
    new_prefix = f"{prefix} {next_word}".strip()
    s1 = s1[len(next_word):].strip()
    return max(
        sentence_similarity_rec(s1, s2, prefix=prefix),
        sentence_similarity_rec(s1, s2, prefix=new_prefix),
    )


def hours_diff(d1: datetime.date, d2: datetime.date) -> int:
    """Calculate the number of hours between two dates."""
    td = d2 - d1
    return td.days * 24 + td.seconds // 3600
