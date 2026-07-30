from sqlalchemy import select

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
    """
    Add or update the complete birthday roster.

    Returns:
        A tuple containing:
        - number of new members created
        - number of existing members updated
        - number of planner assignments updated
    """

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

        # First pass:
        # Create missing members and update birthdays/usernames.
        for entry in BIRTHDAY_ROSTER:
            member_name = entry["name"]
            member_key = member_name.casefold()

            member = members_by_name.get(member_key)

            if member is None:
                member = Member(
                    display_name=member_name,
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

                # Do not erase an existing username when the roster has none.
                if (
                    username is not None
                    and member.telegram_username != username
                ):
                    member.telegram_username = username
                    details_changed = True

                if details_changed:
                    updated_count += 1

        # Assign IDs to newly created members before linking planners.
        session.flush()

        # Second pass:
        # Assign each member's birthday planner.
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