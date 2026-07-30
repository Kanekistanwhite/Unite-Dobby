from sqlalchemy import func, select

from database.database import SessionLocal
from models.member import Member


BIRTHDAY_ROSTER = [
    {
        "name": "Kelly",
        "day": 9,
        "month": 1,
        "username": "youtia0",
        "planner": "Gordon",
    },
    {
        "name": "Jireh",
        "day": 16,
        "month": 1,
        "username": "jeeray",
        "planner": "Sarah",
    },
    {
        "name": "Grace Ee",
        "day": 26,
        "month": 1,
        "username": "eeenqi",
        "planner": "Alythea",
    },
    {
        "name": "Jude",
        "day": 13,
        "month": 2,
        "username": "Shadow3401",
        "planner": "Darrell",
    },
    {
        "name": "Shannyn",
        "day": 27,
        "month": 2,
        "username": "shannynchan",
        "planner": "Gordon",
    },
    {
        "name": "David",
        "day": 22,
        "month": 4,
        "username": "d4vidsng",
        "planner": "Sarah",
    },
    {
        "name": "Ace",
        "day": 8,
        "month": 5,
        "username": "Siuperidoldexiaorong",
        "planner": "Darrell",
    },
    {
        "name": "Darrell",
        "day": 2,
        "month": 6,
        "username": "darrellang",
        "planner": "Gordon",
    },
    {
        "name": "Yun Fei",
        "day": 16,
        "month": 6,
        "username": "yunfeiii",
        "planner": "Sarah",
    },
    {
        "name": "Thiery",
        "day": 5,
        "month": 7,
        "username": "Thieryyy_C",
        "planner": "Alythea",
    },
    {
        "name": "Alythea",
        "day": 2,
        "month": 9,
        "username": "thea_ter",
        "planner": "Darrell",
    },
    {
        "name": "Ann",
        "day": 14,
        "month": 9,
        "username": "annkh00",
        "planner": "Gordon",
    },
    {
        "name": "Clarissa",
        "day": 18,
        "month": 9,
        "username": "clarilah",
        "planner": "Gordon",
    },
    {
        "name": "Ryan Lai",
        "day": 3,
        "month": 10,
        "username": "plslaryan",
        "planner": "Sarah",
    },
    {
        "name": "Eber",
        "day": 5,
        "month": 10,
        "username": "eberfun",
        "planner": "Sarah",
    },
    {
        "name": "Gordon",
        "day": 7,
        "month": 11,
        "username": "gordonwg",
        "planner": "Alythea",
    },
    {
        "name": "Sarah",
        "day": 12,
        "month": 12,
        "username": None,
        "planner": "Darrell",
    },
    {
        "name": "Cheryl Choo",
        "day": 17,
        "month": 12,
        "username": "ineedm0rningsun",
        "planner": "Gordon",
    },
]


def seed_birthday_roster() -> tuple[int, int, int]:
    """Add or update the complete birthday roster."""

    with SessionLocal() as session:
        existing_members = session.scalars(
            select(Member)
        ).all()

        members_by_name = {
            member.display_name.casefold(): member
            for member in existing_members
        }

        created_count = 0
        updated_count = 0
        planner_count = 0

        # First pass: create or update all members.
        for entry in BIRTHDAY_ROSTER:
            member_key = entry["name"].casefold()
            member = members_by_name.get(member_key)

            if member is None:
                member = Member(
                    display_name=entry["name"],
                    birthday_day=entry["day"],
                    birthday_month=entry["month"],
                    telegram_username=entry["username"],
                    is_active=True,
                )

                session.add(member)
                members_by_name[member_key] = member
                created_count += 1

            else:
                details_changed = False

                if member.birthday_day != entry["day"]:
                    member.birthday_day = entry["day"]
                    details_changed = True

                if member.birthday_month != entry["month"]:
                    member.birthday_month = entry["month"]
                    details_changed = True

                if not member.is_active:
                    member.is_active = True
                    details_changed = True

                username = entry["username"]

                if (
                    username is not None
                    and member.telegram_username != username
                ):
                    member.telegram_username = username
                    details_changed = True

                if details_changed:
                    updated_count += 1

        # Give newly created members their database IDs.
        session.flush()

        # Second pass: assign birthday planners.
        for entry in BIRTHDAY_ROSTER:
            member = members_by_name[
                entry["name"].casefold()
            ]

            planner = members_by_name[
                entry["planner"].casefold()
            ]

            if member.birthday_planner_id != planner.id:
                member.birthday_planner_id = planner.id
                planner_count += 1

        session.commit()

        return (
            created_count,
            updated_count,
            planner_count,
        )


def get_birthdays_for_date(
    day: int,
    month: int,
) -> list[tuple[str, str | None]]:
    """Return active members whose birthday matches a date."""

    with SessionLocal() as session:
        rows = session.execute(
            select(
                Member.display_name,
                Member.telegram_username,
            )
            .where(
                Member.is_active.is_(True),
                Member.birthday_day == day,
                Member.birthday_month == month,
            )
            .order_by(Member.display_name)
        ).all()

        return [
            (display_name, telegram_username)
            for display_name, telegram_username in rows
        ]


def get_birthday_member_by_name(
    display_name: str,
) -> tuple[str, str | None] | None:
    """Find an active member by display name."""

    cleaned_name = display_name.strip()

    if not cleaned_name:
        return None

    with SessionLocal() as session:
        row = session.execute(
            select(
                Member.display_name,
                Member.telegram_username,
            )
            .where(
                Member.is_active.is_(True),
                func.lower(Member.display_name)
                == cleaned_name.lower(),
            )
        ).one_or_none()

        if row is None:
            return None

        return row[0], row[1]