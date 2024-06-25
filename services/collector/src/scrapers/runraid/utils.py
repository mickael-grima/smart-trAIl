from datetime import date, datetime


def parse_date(text: str) -> date:
    return datetime.strptime(text, "%d-%m-%Y").date()
