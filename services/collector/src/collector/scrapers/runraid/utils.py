from datetime import date, datetime


def parse_date(text: str) -> date:
    """
    Parse date from text.

    Examples
    --------
    parse_date("8-6-2025")
    >> date(year=2025, month=6, date=8)
    """
    return datetime.strptime(text, "%d-%m-%Y").date()  # noqa: DTZ007
