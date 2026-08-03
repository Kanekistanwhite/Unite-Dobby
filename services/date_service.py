from calendar import (
    day_abbr,
    day_name,
    month_abbr,
    month_name,
)
from datetime import date, timedelta


def format_full_date(
    value: date,
) -> str:
    """
    Format a date as:

    Saturday, 8 August 2026
    """

    weekday = day_name[value.weekday()]
    month = month_name[value.month]

    return (
        f"{weekday}, "
        f"{value.day} "
        f"{month} "
        f"{value.year}"
    )


def format_short_date(
    value: date,
) -> str:
    """
    Format a date as:

    Sat, 8 Aug 2026
    """

    weekday = day_abbr[value.weekday()]
    month = month_abbr[value.month]

    return (
        f"{weekday}, "
        f"{value.day} "
        f"{month} "
        f"{value.year}"
    )


def get_upcoming_sunday(
    reference_date: date | None = None,
) -> date:
    """
    Return the upcoming Sunday.

    When the reference date is already Sunday,
    that same date is returned.
    """

    current_date = reference_date or date.today()

    # Python weekday values:
    # Monday = 0, Sunday = 6.
    days_until_sunday = (
        6 - current_date.weekday()
    ) % 7

    return current_date + timedelta(
        days=days_until_sunday
    )