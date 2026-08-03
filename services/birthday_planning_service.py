from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from database.database import SessionLocal
from models.member import Member


@dataclass(frozen=True)
class BirthdayPlanningMember:
    """Birthday and assigned-planner information."""

    display_name: str
    birthday_day: int
    birthday_month: int
    planner_name: str
    planner_username: str | None


@dataclass(frozen=True)
class BirthdayPlanningReminder:
    """A birthday reminder that is due on a specific date."""

    member: BirthdayPlanningMember
    birthday_date: date
    reminder_type: str


def create_birthday_date(
    year: int,
    month: int,
    day: int,
) -> date:
    """
    Create a birthday date safely.

    A 29 February birthday falls on 28 February
    during a non-leap year.
    """

    maximum_day = monthrange(
        year,
        month,
    )[1]

    safe_day = min(
        day,
        maximum_day,
    )

    return date(
        year,
        month,
        safe_day,
    )


def get_next_birthday_date(
    birthday_day: int,
    birthday_month: int,
    reference_date: date,
) -> date:
    """Return the member's next birthday."""

    birthday_date = create_birthday_date(
        year=reference_date.year,
        month=birthday_month,
        day=birthday_day,
    )

    if birthday_date < reference_date:
        birthday_date = create_birthday_date(
            year=reference_date.year + 1,
            month=birthday_month,
            day=birthday_day,
        )

    return birthday_date


def subtract_one_calendar_month(
    value: date,
) -> date:
    """Return the date one calendar month before a date."""

    year = value.year
    month = value.month - 1

    if month == 0:
        year -= 1
        month = 12

    maximum_day = monthrange(
        year,
        month,
    )[1]

    return date(
        year,
        month,
        min(value.day, maximum_day),
    )


def get_birthday_planning_member_by_name(
    display_name: str,
) -> BirthdayPlanningMember | None:
    """Find a member and their assigned birthday planner."""

    cleaned_name = display_name.strip()

    if not cleaned_name:
        return None

    planner = aliased(Member)

    with SessionLocal() as session:
        row = session.execute(
            select(
                Member.display_name,
                Member.birthday_day,
                Member.birthday_month,
                planner.display_name,
                planner.telegram_username,
            )
            .join(
                planner,
                Member.birthday_planner_id == planner.id,
            )
            .where(
                Member.is_active.is_(True),
                Member.birthday_day.is_not(None),
                Member.birthday_month.is_not(None),
                func.lower(Member.display_name)
                == cleaned_name.lower(),
            )
        ).one_or_none()

        if row is None:
            return None

        return BirthdayPlanningMember(
            display_name=row[0],
            birthday_day=int(row[1]),
            birthday_month=int(row[2]),
            planner_name=row[3],
            planner_username=row[4],
        )


def get_all_birthday_planning_members(
) -> list[BirthdayPlanningMember]:
    """Return all active members with assigned planners."""

    planner = aliased(Member)

    with SessionLocal() as session:
        rows = session.execute(
            select(
                Member.display_name,
                Member.birthday_day,
                Member.birthday_month,
                planner.display_name,
                planner.telegram_username,
            )
            .join(
                planner,
                Member.birthday_planner_id == planner.id,
            )
            .where(
                Member.is_active.is_(True),
                Member.birthday_day.is_not(None),
                Member.birthday_month.is_not(None),
            )
            .order_by(
                Member.birthday_month,
                Member.birthday_day,
                Member.display_name,
            )
        ).all()

        return [
            BirthdayPlanningMember(
                display_name=row[0],
                birthday_day=int(row[1]),
                birthday_month=int(row[2]),
                planner_name=row[3],
                planner_username=row[4],
            )
            for row in rows
        ]


def get_birthday_planning_reminders_for_date(
    reference_date: date,
) -> list[BirthdayPlanningReminder]:
    """Return one-month and two-week reminders due today."""

    reminders: list[BirthdayPlanningReminder] = []

    for member in get_all_birthday_planning_members():
        birthday_date = get_next_birthday_date(
            birthday_day=member.birthday_day,
            birthday_month=member.birthday_month,
            reference_date=reference_date,
        )

        one_month_reminder_date = subtract_one_calendar_month(
            birthday_date
        )

        two_week_reminder_date = (
            birthday_date - timedelta(days=14)
        )

        if reference_date == one_month_reminder_date:
            reminders.append(
                BirthdayPlanningReminder(
                    member=member,
                    birthday_date=birthday_date,
                    reminder_type="month",
                )
            )

        if reference_date == two_week_reminder_date:
            reminders.append(
                BirthdayPlanningReminder(
                    member=member,
                    birthday_date=birthday_date,
                    reminder_type="fortnight",
                )
            )

    return reminders