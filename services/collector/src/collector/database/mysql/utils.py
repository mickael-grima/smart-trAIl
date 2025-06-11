from datetime import timedelta


def format_timedelta(td: timedelta) -> str:
    """
    Convert timedelta into HH:MM:SS string.

    Returns
    -------
    str
        A time as a string: HH:MM:SS format.
    """
    td_in_seconds = td.total_seconds()
    hours, remainder = divmod(td_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
