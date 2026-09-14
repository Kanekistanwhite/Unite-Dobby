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
from models.care_birthday_reminder import CareBirthdayReminder


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


CARE_BIRTHDAY_PREP_CHECKLIST = {
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


CARE_BIRTHDAY_WORKFLOW_CHECKLIST = {
    "announcement": (
        "monthly_announcement_sent",
        "Monthly birthday announcement sent",
    ),
    "celebration": (
        "celebration_completed",
        "Birthday celebration completed",
    ),
    "distribution": (
        "distribution_completed",
        "Distribution completed",
    ),
}


CARE_BIRTHDAY_ALL_CHECKLIST = {
    **CARE_BIRTHDAY_PREP_CHECKLIST,
    **CARE_BIRTHDAY_WORKFLOW_CHECKLIST,
}


def get_singapore_now() -> datetime:
    """Return current Singapore time."""

    return datetime.now(
        SINGAPORE_TIMEZONE
    ).replace(
        tzinfo=None
    )


def seed_care_birthday_roster() -> tuple[int, int]:
    """Create or update CARE Birthday roster."""

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
                session.add(
                    CareBirthdayMember(
                        display_name=display_name,
                        birthday_day=birthday_day,
                        birthday_month=birthday_month,
                        is_active=True,
                    )
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
    """Return CARE Birthday celebrants for one month."""

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
    """Calculate first Sunday of month."""

    first_day = date(
        year,
        month,
        1,
    )

    days_until_sunday = (
        6 - first_day.weekday()
    ) % 7

    return first_day + timedelta(
        days=days_until_sunday
    )


def get_next_month(
    year: int,
    month: int,
) -> tuple[int, int]:
    """Return the following year/month."""

    if month == 12:
        return (
            year + 1,
            1,
        )

    return (
        year,
        month + 1,
    )


def get_current_care_birthday_period() -> tuple[int, int]:
    """Return the batch currently being prepared."""

    now = get_singapore_now()

    if now.day == 1:
        return (
            now.year,
            now.month,
        )

    return get_next_month(
        now.year,
        now.month,
    )


def get_or_create_care_birthday_batch(
    year: int,
    month: int,
) -> CareBirthdayBatch:
    """Get or create monthly CARE Birthday batch."""

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
    """Toggle one CARE Birthday checklist item."""

    checklist_item = CARE_BIRTHDAY_ALL_CHECKLIST.get(
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


def get_incomplete_preparation_items(
    batch: CareBirthdayBatch,
) -> list[str]:
    """Return unfinished preparation checklist labels."""

    incomplete = []

    for (
        field_name,
        label,
    ) in CARE_BIRTHDAY_PREP_CHECKLIST.values():

        if not getattr(
            batch,
            field_name,
        ):
            incomplete.append(
                label
            )

    return incomplete


def has_care_birthday_reminder_been_sent(
    year: int,
    month: int,
    reminder_type: str,
) -> bool:
    """Check whether a specific reminder was already sent."""

    with SessionLocal() as session:
        reminder = session.scalar(
            select(CareBirthdayReminder).where(
                CareBirthdayReminder.year == year,
                CareBirthdayReminder.month == month,
                CareBirthdayReminder.reminder_type
                == reminder_type,
            )
        )

        return reminder is not None


def record_care_birthday_reminder_sent(
    year: int,
    month: int,
    reminder_type: str,
) -> None:
    """Record successful CARE Birthday reminder."""

    with SessionLocal() as session:

        existing = session.scalar(
            select(CareBirthdayReminder).where(
                CareBirthdayReminder.year == year,
                CareBirthdayReminder.month == month,
                CareBirthdayReminder.reminder_type
                == reminder_type,
            )
        )

        if existing is not None:
            return

        session.add(
            CareBirthdayReminder(
                year=year,
                month=month,
                reminder_type=reminder_type,
                sent_at=get_singapore_now(),
            )
        )

        session.commit()


def format_celebrant_list(
    month: int,
) -> str:
    """Format all celebrants for one month."""

    members = get_care_birthdays_for_month(
        month
    )

    if not members:
        return "• No registered celebrants"

    lines = []

    for member in members:
        short_month = month_name[
            member.birthday_month
        ][:3]

        lines.append(
            f"• {member.display_name} — "
            f"{member.birthday_day} {short_month}"
        )

    return "\n".join(
        lines
    )


def format_care_birthday_month(
    year: int,
    month: int,
) -> str:
    """Format monthly CARE Birthday summary."""

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
        format_celebrant_list(
            month
        ),
        "",
        f"👥 {len(members)} celebrant"
        f"{'' if len(members) == 1 else 's'}",
        "",
        "🥳 Celebration:",
        (
            f"{celebration_date.strftime('%A')}, "
            f"{celebration_date.day} "
            f"{celebration_date.strftime('%B %Y')}"
        ),
    ]

    return "\n".join(
        lines
    )


def format_care_birthday_batch(
    year: int,
    month: int,
) -> str:
    """Format complete CARE Birthday batch."""

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

    preparation_values = [
        getattr(
            batch,
            field_name,
        )
        for (
            field_name,
            label,
        )
        in CARE_BIRTHDAY_PREP_CHECKLIST.values()
    ]

    if (
        all(preparation_values)
        and batch.monthly_announcement_sent
        and batch.celebration_completed
        and batch.distribution_completed
    ):
        status = "✅ Month Completed"

    elif batch.celebration_completed:
        status = "🟠 Distribution Pending"

    elif any(preparation_values):
        status = "🟡 In Progress"

    else:
        status = "⚪ Not Started"

    lines = [
        f"🎂 {month_name[month].upper()} {year} BIRTHDAY BATCH",
        "",
        status,
        "",
        "👥 Celebrants:",
        format_celebrant_list(
            month
        ),
        "",
        f"👥 Total: {len(members)}",
        "",
        "📋 Preparation:",
    ]

    for (
        field_name,
        label,
    ) in CARE_BIRTHDAY_PREP_CHECKLIST.values():

        completed = getattr(
            batch,
            field_name,
        )

        lines.append(
            f"{'✅' if completed else '⬜'} {label}"
        )

    lines.extend(
        [
            "",
            "🎉 Birthday Month:",
        ]
    )

    for (
        field_name,
        label,
    ) in CARE_BIRTHDAY_WORKFLOW_CHECKLIST.values():

        completed = getattr(
            batch,
            field_name,
        )

        lines.append(
            f"{'✅' if completed else '⬜'} {label}"
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