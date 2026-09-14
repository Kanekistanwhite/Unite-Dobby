from calendar import month_name
from datetime import (
    date,
    datetime,
    timedelta,
)
from zoneinfo import ZoneInfo

from sqlalchemy import (
    func,
    select,
)

from database.database import SessionLocal
from models.care_birthday_batch import CareBirthdayBatch
from models.care_birthday_member import CareBirthdayMember


SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


CARE_BIRTHDAY_ROSTER = [
    # January
    ("Moses Teng", 7, 1),
    ("Moses Koh", 8, 1),
    ("Wallace Wong", 9, 1),
    ("Gerald Tham", 11, 1),
    ("Jing Jing", 11, 1),
    ("Jireh Tham", 16, 1),
    ("Grace Ee", 26, 1),
    ("Jenevieve Chng", 26, 1),

    # February
    ("Jude", 13, 2),
    ("Shannon Ang", 14, 2),
    ("Charlotte Poon", 17, 2),
    ("Zanna Ker", 21, 2),

    # March
    ("Lucas Peck", 23, 3),
    ("Titus Lua", 30, 3),

    # April
    ("Alyssa Lim", 3, 4),
    ("Malchus Teng", 4, 4),
    ("Kieran Da Silva", 6, 4),
    ("Ezanne Sim", 11, 4),
    ("Anson the hansom", 14, 4),
    ("Cheyenne", 20, 4),
    ("David Sng", 22, 4),
    ("Loh Kay Dan", 28, 4),
    ("Meihui", 28, 4),

    # May
    ("Ace Koh", 8, 5),
    ("Alice", 12, 5),
    ("Chantalle Low (Quinn)", 16, 5),

    # June
    ("Darrell Ang", 2, 6),
    ("Gratus Aw", 11, 6),
    ("Yun Fei", 16, 6),
    ("Asher Poh", 19, 6),

    # July
    ("Loh Kay Lyn", 1, 7),
    ("Tiffany Teo", 1, 7),
    ("Janias Tan", 5, 7),
    ("Thiery Chin", 5, 7),
    ("Charis Poon", 7, 7),
    ("Katelyn Da Silva", 14, 7),
    ("Jedidiah Tan", 17, 7),
    ("Gabriel Chia", 23, 7),
    ("Kayden Tan", 30, 7),

    # August
    ("Nigel Wong", 2, 8),
    ("Lim Jia Xuan", 11, 8),
    ("Claire Cher", 24, 8),
    ("Cheryl Teo", 28, 8),

    # September
    ("Alythea Koh", 2, 9),
    ("Mavis Cham", 3, 9),
    ("Rachel Ng", 8, 9),
    ("Terence Chin", 13, 9),
    ("Khoo Ann Yee", 14, 9),
    ("Clarissa Ee", 18, 9),
    ("Teng Christy", 23, 9),

    # October
    ("Ryan Lai", 3, 10),
    ("Eber", 5, 10),
    ("Abrielle Koh", 6, 10),
    ("Elliot Seow", 7, 10),
    ("Garina Peck", 9, 10),
    ("Maegan Cham", 10, 10),
    ("Jaidyn Tan", 14, 10),
    ("Law Yi Xiang", 15, 10),
    ("Matthias Teng", 29, 10),
    ("Hannah Lim", 31, 10),

    # November
    ("Gordon Wong", 7, 11),
    ("Lewis Low", 18, 11),
    ("Christel Poon", 24, 11),
    ("Declan Koh", 27, 11),
    ("Abbey Poh", 30, 11),
    ("Leia", 30, 11),

    # December
    ("Daius Koh", 7, 12),
    ("Gabriel Choo", 9, 12),
    ("Sarah Lim", 12, 12),
    ("Ethan Macaraig", 21, 12),
]


CARE_BIRTHDAY_CHECKLIST = {
    "celebrants": (
        "celebrant_list_confirmed",
        "Celebrant list confirmed",
    ),
    "idea": (
        "celebration_idea_ready",
        "Celebration idea ready",
    ),
    "cake": (
        "cake_arranged",
        "Cake arranged",
    ),
    "gifts": (
        "gift_packs_ready",
        "Gift packs ready",
    ),
    "cards": (
        "birthday_cards_ready",
        "Birthday cards ready",
    ),
}


def seed_care_birthday_roster() -> tuple[int, int]:
    """Create or update the CARE Birthday roster."""

    created = 0
    updated = 0

    with SessionLocal() as session:

        for (
            display_name,
            birthday_day,
            birthday_month,
        ) in CARE_BIRTHDAY_ROSTER:

            existing = session.scalar(
                select(CareBirthdayMember).where(
                    func.lower(
                        CareBirthdayMember.display_name
                    )
                    == display_name.lower()
                )
            )

            if existing is None:
                member = CareBirthdayMember(
                    display_name=display_name,
                    birthday_day=birthday_day,
                    birthday_month=birthday_month,
                    is_active=True,
                )

                session.add(
                    member
                )

                created += 1

            else:
                existing.birthday_day = birthday_day
                existing.birthday_month = birthday_month
                existing.is_active = True

                updated += 1

        session.commit()

    return created, updated


def get_care_birthdays_for_month(
    month: int,
) -> list[CareBirthdayMember]:
    """Return active CARE Birthday members for one month."""

    if month < 1 or month > 12:
        raise ValueError(
            "Month must be between 1 and 12."
        )

    with SessionLocal() as session:
        members = session.scalars(
            select(CareBirthdayMember)
            .where(
                CareBirthdayMember.is_active.is_(True),
                CareBirthdayMember.birthday_month == month,
            )
            .order_by(
                CareBirthdayMember.birthday_day,
                CareBirthdayMember.display_name,
            )
        ).all()

        return list(
            members
        )


def get_first_sunday(
    year: int,
    month: int,
) -> date:
    """Calculate the first Sunday of a month."""

    current_date = date(
        year,
        month,
        1,
    )

    days_until_sunday = (
        6 - current_date.weekday()
    ) % 7

    return current_date + timedelta(
        days=days_until_sunday
    )


def get_current_care_birthday_period() -> tuple[int, int]:
    """
    Return the month currently being prepared.

    On the 1st, Dobby still treats the current month as active.
    From the 2nd onward, preparation moves to the next month.
    """

    now = datetime.now(
        SINGAPORE_TIMEZONE
    )

    if now.day == 1:
        return (
            now.year,
            now.month,
        )

    if now.month == 12:
        return (
            now.year + 1,
            1,
        )

    return (
        now.year,
        now.month + 1,
    )


def get_or_create_care_birthday_batch(
    year: int,
    month: int,
) -> CareBirthdayBatch:
    """Get or create one monthly CARE Birthday batch."""

    # Validate year/month.
    date(
        year,
        month,
        1,
    )

    with SessionLocal() as session:
        batch = session.scalar(
            select(CareBirthdayBatch).where(
                CareBirthdayBatch.year == year,
                CareBirthdayBatch.month == month,
            )
        )

        if batch is None:
            batch = CareBirthdayBatch(
                year=year,
                month=month,
            )

            session.add(
                batch
            )

            session.commit()
            session.refresh(
                batch
            )

        return batch


def toggle_care_birthday_checklist_item(
    year: int,
    month: int,
    item_key: str,
) -> CareBirthdayBatch:
    """Toggle one preparation checklist item."""

    checklist_item = CARE_BIRTHDAY_CHECKLIST.get(
        item_key
    )

    if checklist_item is None:
        raise ValueError(
            "Unknown CARE Birthday checklist item."
        )

    field_name = checklist_item[0]

    with SessionLocal() as session:
        batch = session.scalar(
            select(CareBirthdayBatch).where(
                CareBirthdayBatch.year == year,
                CareBirthdayBatch.month == month,
            )
        )

        if batch is None:
            batch = CareBirthdayBatch(
                year=year,
                month=month,
            )

            session.add(
                batch
            )

            session.flush()

        current_value = getattr(
            batch,
            field_name,
        )

        setattr(
            batch,
            field_name,
            not current_value,
        )

        batch.updated_at = datetime.now()

        session.commit()
        session.refresh(
            batch
        )

        return batch


def format_care_birthday_month(
    year: int,
    month: int,
) -> str:
    """Create a readable monthly birthday summary."""

    members = get_care_birthdays_for_month(
        month
    )

    celebration_date = get_first_sunday(
        year,
        month,
    )

    lines = [
        f"🎂 {month_name[month].upper()} {year} BIRTHDAYS",
        "",
    ]

    if not members:
        lines.append(
            "No celebrants are registered for this month."
        )

    else:
        for member in members:
            short_month = month_name[
                member.birthday_month
            ][:3]

            lines.append(
                f"• {member.display_name} — "
                f"{member.birthday_day} {short_month}"
            )

        lines.extend(
            [
                "",
                f"👥 {len(members)} celebrant"
                f"{'' if len(members) == 1 else 's'}",
            ]
        )

    lines.extend(
        [
            "",
            "🥳 Celebration:",
            (
                f"{celebration_date.strftime('%A')}, "
                f"{celebration_date.day} "
                f"{celebration_date.strftime('%B %Y')}"
            ),
        ]
    )

    return "\n".join(
        lines
    )


def format_care_birthday_batch(
    year: int,
    month: int,
) -> str:
    """Create the monthly CARE Birthday batch summary."""

    members = get_care_birthdays_for_month(
        month
    )

    batch = get_or_create_care_birthday_batch(
        year,
        month,
    )

    celebration_date = get_first_sunday(
        year,
        month,
    )

    checklist_values = []

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in CARE_BIRTHDAY_CHECKLIST.items():

        completed = getattr(
            batch,
            field_name,
        )

        checklist_values.append(
            completed
        )

    if all(
        checklist_values
    ):
        status = "🟢 Preparation Complete"

    elif any(
        checklist_values
    ):
        status = "🟡 In Progress"

    else:
        status = "⚪ Not Started"

    lines = [
        f"🎂 {month_name[month].upper()} {year} BIRTHDAY BATCH",
        "",
        status,
        "",
        "👥 Celebrants:",
    ]

    if members:
        for member in members:
            short_month = month_name[
                member.birthday_month
            ][:3]

            lines.append(
                f"• {member.display_name} — "
                f"{member.birthday_day} {short_month}"
            )
    else:
        lines.append(
            "• No registered celebrants"
        )

    lines.extend(
        [
            "",
            f"👥 Total: {len(members)}",
            "",
            "📋 Preparation Checklist:",
        ]
    )

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in CARE_BIRTHDAY_CHECKLIST.items():

        completed = getattr(
            batch,
            field_name,
        )

        icon = (
            "✅"
            if completed
            else "⬜"
        )

        lines.append(
            f"{icon} {label}"
        )

    lines.extend(
        [
            "",
            "🥳 Celebration:",
            (
                f"{celebration_date.strftime('%A')}, "
                f"{celebration_date.day} "
                f"{celebration_date.strftime('%B %Y')}"
            ),
        ]
    )

    return "\n".join(
        lines
    )