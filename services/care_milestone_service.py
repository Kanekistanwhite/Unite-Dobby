from calendar import (
    month_name,
    monthrange,
)
from datetime import (
    date,
    datetime,
    timedelta,
)
from zoneinfo import ZoneInfo

from sqlalchemy import (
    delete,
    select,
)

from database.database import SessionLocal
from models.care_milestone import CareMilestone
from models.care_milestone_annual_plan import (
    CareMilestoneAnnualPlan,
)
from models.care_milestone_reminder import (
    CareMilestoneReminder,
)


SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


# =========================================================
# MILESTONE TYPES
# =========================================================

MILESTONE_TYPES = {
    "secondary": {
        "label": "Secondary School Graduation",
        "emoji": "🎓",
        "aliases": {
            "secondary",
            "secondary school",
            "sec",
            "sec school",
        },
    },
    "polytechnic": {
        "label": "Polytechnic Graduation",
        "emoji": "🎓",
        "aliases": {
            "polytechnic",
            "poly",
        },
    },
    "jc": {
        "label": "JC Graduation",
        "emoji": "🎓",
        "aliases": {
            "jc",
            "junior college",
        },
    },
    "university": {
        "label": "University Graduation",
        "emoji": "🎓",
        "aliases": {
            "university",
            "uni",
        },
    },
    "baptism": {
        "label": "Baptism",
        "emoji": "✝️",
        "aliases": {
            "baptism",
            "baptised",
            "baptized",
        },
    },
    "ord": {
        "label": "ORD",
        "emoji": "🪖",
        "aliases": {
            "ord",
            "army",
        },
    },
}


MILESTONE_CHECKLIST = {
    "giftprep": (
        "gift_prepared",
        "Gift prepared",
    ),
    "cardprep": (
        "card_prepared",
        "Card prepared",
    ),
    "giftgiven": (
        "gift_given",
        "Gift given",
    ),
    "cardgiven": (
        "card_given",
        "Card given",
    ),
}


ANNUAL_GIFT_FIELDS = {
    "secondary": "secondary_gift",
    "polytechnic": "polytechnic_gift",
    "jc": "jc_gift",
    "university": "university_gift",
    "baptism": "baptism_gift",
    "ord": "ord_gift",
}


# =========================================================
# TIME
# =========================================================

def get_singapore_today() -> date:
    """Return today's Singapore date."""

    return datetime.now(
        SINGAPORE_TIMEZONE
    ).date()


# =========================================================
# TYPE HELPERS
# =========================================================

def normalise_milestone_type(
    value: str,
) -> str:
    """Convert milestone type input into canonical key."""

    cleaned = " ".join(
        value.strip().lower().split()
    )

    for (
        type_key,
        type_info,
    ) in MILESTONE_TYPES.items():

        if cleaned in type_info["aliases"]:
            return type_key

    raise ValueError(
        "Unknown milestone type."
    )


def get_milestone_type_label(
    milestone_type: str,
) -> str:
    """Return friendly milestone label."""

    type_info = MILESTONE_TYPES.get(
        milestone_type
    )

    if type_info is None:
        return milestone_type.title()

    return type_info["label"]


def get_milestone_type_emoji(
    milestone_type: str,
) -> str:
    """Return milestone emoji."""

    type_info = MILESTONE_TYPES.get(
        milestone_type
    )

    if type_info is None:
        return "🏆"

    return type_info["emoji"]


# =========================================================
# DATE HELPERS
# =========================================================

def parse_milestone_date(
    value: str,
) -> tuple[
    int,
    int,
    date | None,
]:
    """
    Accept either:
    DD-MM-YYYY
    MM-YYYY
    """

    cleaned = value.strip()

    parts = cleaned.split(
        "-"
    )

    if len(parts) == 3:

        day = int(
            parts[0]
        )

        month = int(
            parts[1]
        )

        year = int(
            parts[2]
        )

        exact_date = date(
            year,
            month,
            day,
        )

        return (
            year,
            month,
            exact_date,
        )

    if len(parts) == 2:

        month = int(
            parts[0]
        )

        year = int(
            parts[1]
        )

        date(
            year,
            month,
            1,
        )

        return (
            year,
            month,
            None,
        )

    raise ValueError(
        "Date must be DD-MM-YYYY or MM-YYYY."
    )


def subtract_one_calendar_month(
    source_date: date,
) -> date:
    """Return one calendar month before a date."""

    if source_date.month == 1:
        year = source_date.year - 1
        month = 12

    else:
        year = source_date.year
        month = source_date.month - 1

    last_day = monthrange(
        year,
        month,
    )[1]

    day = min(
        source_date.day,
        last_day,
    )

    return date(
        year,
        month,
        day,
    )


def previous_month_first_day(
    year: int,
    month: int,
) -> date:
    """Return first day of previous month."""

    if month == 1:
        return date(
            year - 1,
            12,
            1,
        )

    return date(
        year,
        month - 1,
        1,
    )


# =========================================================
# MILESTONE CRUD
# =========================================================

def add_milestone(
    person_name: str,
    milestone_type: str,
    date_value: str,
) -> CareMilestone:
    """Create a new CARE milestone."""

    cleaned_name = " ".join(
        person_name.strip().split()
    )

    if not cleaned_name:
        raise ValueError(
            "Person name is required."
        )

    type_key = normalise_milestone_type(
        milestone_type
    )

    (
        year,
        month,
        exact_date,
    ) = parse_milestone_date(
        date_value
    )

    with SessionLocal() as session:

        milestone = CareMilestone(
            person_name=cleaned_name,
            milestone_type=type_key,
            milestone_year=year,
            milestone_month=month,
            milestone_date=exact_date,
        )

        session.add(
            milestone
        )

        session.commit()
        session.refresh(
            milestone
        )

        return milestone


def get_milestone(
    milestone_id: int,
) -> CareMilestone | None:
    """Get one milestone by ID."""

    with SessionLocal() as session:

        return session.get(
            CareMilestone,
            milestone_id,
        )


def update_milestone_date(
    milestone_id: int,
    date_value: str,
) -> CareMilestone:
    """
    Update a milestone from month-only to exact date,
    or change an existing date.

    Reminder state is reset so Dobby can calculate
    the new reminder dates.
    """

    (
        year,
        month,
        exact_date,
    ) = parse_milestone_date(
        date_value
    )

    with SessionLocal() as session:

        milestone = session.get(
            CareMilestone,
            milestone_id,
        )

        if milestone is None:
            raise ValueError(
                "Milestone not found."
            )

        milestone.milestone_year = year
        milestone.milestone_month = month
        milestone.milestone_date = exact_date
        milestone.planning_reminder_sent = False
        milestone.updated_at = datetime.now()

        session.execute(
            delete(
                CareMilestoneReminder
            ).where(
                CareMilestoneReminder.reminder_type
                == f"two_week:{milestone_id}"
            )
        )

        session.commit()
        session.refresh(
            milestone
        )

        return milestone


def get_milestones_for_year(
    year: int,
    include_completed: bool = True,
) -> list[CareMilestone]:
    """Return milestones for one year."""

    with SessionLocal() as session:

        milestones = session.scalars(
            select(
                CareMilestone
            )
            .where(
                CareMilestone.milestone_year == year,
                CareMilestone.is_cancelled.is_(False),
            )
            .order_by(
                CareMilestone.milestone_month,
                CareMilestone.milestone_date,
                CareMilestone.person_name,
            )
        ).all()

        result = list(
            milestones
        )

        if not include_completed:

            result = [
                milestone
                for milestone in result
                if not is_milestone_complete(
                    milestone
                )
            ]

        return result


def get_milestones_for_month(
    year: int,
    month: int,
    include_completed: bool = True,
) -> list[CareMilestone]:
    """Return milestones for one month."""

    date(
        year,
        month,
        1,
    )

    with SessionLocal() as session:

        milestones = session.scalars(
            select(
                CareMilestone
            )
            .where(
                CareMilestone.milestone_year == year,
                CareMilestone.milestone_month == month,
                CareMilestone.is_cancelled.is_(False),
            )
            .order_by(
                CareMilestone.milestone_date,
                CareMilestone.person_name,
            )
        ).all()

        result = list(
            milestones
        )

        if not include_completed:

            result = [
                milestone
                for milestone in result
                if not is_milestone_complete(
                    milestone
                )
            ]

        return result


def get_active_milestones() -> list[CareMilestone]:
    """Return unfinished milestones."""

    with SessionLocal() as session:

        milestones = session.scalars(
            select(
                CareMilestone
            )
            .where(
                CareMilestone.is_cancelled.is_(False),
            )
            .order_by(
                CareMilestone.milestone_year,
                CareMilestone.milestone_month,
                CareMilestone.milestone_date,
                CareMilestone.person_name,
            )
        ).all()

        return [
            milestone
            for milestone in milestones
            if not is_milestone_complete(
                milestone
            )
        ]


def get_completed_milestones(
    year: int,
) -> list[CareMilestone]:
    """Return completed milestones for history."""

    milestones = get_milestones_for_year(
        year
    )

    return [
        milestone
        for milestone in milestones
        if is_milestone_complete(
            milestone
        )
    ]


# =========================================================
# CHECKLIST
# =========================================================

def toggle_milestone_checklist_item(
    milestone_id: int,
    item_key: str,
) -> CareMilestone:
    """Toggle milestone checklist item."""

    item = MILESTONE_CHECKLIST.get(
        item_key
    )

    if item is None:
        raise ValueError(
            "Unknown milestone checklist item."
        )

    field_name = item[0]

    with SessionLocal() as session:

        milestone = session.get(
            CareMilestone,
            milestone_id,
        )

        if milestone is None:
            raise ValueError(
                "Milestone not found."
            )

        current_value = getattr(
            milestone,
            field_name,
        )

        setattr(
            milestone,
            field_name,
            not current_value,
        )

        milestone.updated_at = datetime.now()

        session.commit()
        session.refresh(
            milestone
        )

        return milestone


def is_milestone_complete(
    milestone: CareMilestone,
) -> bool:
    """Complete when both gift and card were given."""

    return (
        milestone.gift_given
        and milestone.card_given
    )


def cancel_milestone(
    milestone_id: int,
) -> bool:
    """Cancel milestone."""

    with SessionLocal() as session:

        milestone = session.get(
            CareMilestone,
            milestone_id,
        )

        if milestone is None:
            return False

        milestone.is_cancelled = True
        milestone.updated_at = datetime.now()

        session.commit()

        return True


# =========================================================
# REMINDER HISTORY
# =========================================================

def milestone_reminder_was_sent(
    year: int,
    month: int,
    reminder_type: str,
) -> bool:
    """Check reminder history."""

    with SessionLocal() as session:

        reminder = session.scalar(
            select(
                CareMilestoneReminder
            ).where(
                CareMilestoneReminder.year == year,
                CareMilestoneReminder.month == month,
                CareMilestoneReminder.reminder_type
                == reminder_type,
            )
        )

        return reminder is not None


def record_milestone_reminder_sent(
    year: int,
    month: int,
    reminder_type: str,
) -> None:
    """Record reminder as sent."""

    with SessionLocal() as session:

        existing = session.scalar(
            select(
                CareMilestoneReminder
            ).where(
                CareMilestoneReminder.year == year,
                CareMilestoneReminder.month == month,
                CareMilestoneReminder.reminder_type
                == reminder_type,
            )
        )

        if existing is not None:
            return

        session.add(
            CareMilestoneReminder(
                year=year,
                month=month,
                reminder_type=reminder_type,
                sent_at=datetime.now(),
            )
        )

        session.commit()


def mark_planning_reminder_sent(
    milestone_id: int,
) -> None:
    """Mark one-month reminder as handled."""

    with SessionLocal() as session:

        milestone = session.get(
            CareMilestone,
            milestone_id,
        )

        if milestone is None:
            return

        milestone.planning_reminder_sent = True
        milestone.updated_at = datetime.now()

        session.commit()


# =========================================================
# FORMAT INDIVIDUAL
# =========================================================

def format_milestone_date(
    milestone: CareMilestone,
) -> str:
    """Format exact or month-only date."""

    if milestone.milestone_date is not None:

        return milestone.milestone_date.strftime(
            "%d %b %Y"
        )

    return (
        f"{month_name[milestone.milestone_month]} "
        f"{milestone.milestone_year}"
    )


def format_milestone(
    milestone: CareMilestone,
) -> str:
    """Format one milestone."""

    emoji = get_milestone_type_emoji(
        milestone.milestone_type
    )

    label = get_milestone_type_label(
        milestone.milestone_type
    )

    if is_milestone_complete(
        milestone
    ):
        status = "✅ COMPLETED"

    elif (
        milestone.gift_prepared
        or milestone.card_prepared
        or milestone.gift_given
        or milestone.card_given
    ):
        status = "🟡 PREPARING"

    else:
        status = "⚪ NOT STARTED"

    return (
        f"🏆 MILESTONE #{milestone.id}\n\n"
        f"👤 {milestone.person_name}\n"
        f"{emoji} {label}\n"
        f"📅 {format_milestone_date(milestone)}\n\n"
        f"{status}\n\n"
        f"{'✅' if milestone.gift_prepared else '⬜'} "
        "Gift prepared\n"
        f"{'✅' if milestone.card_prepared else '⬜'} "
        "Card prepared\n"
        f"{'✅' if milestone.gift_given else '⬜'} "
        "Gift given\n"
        f"{'✅' if milestone.card_given else '⬜'} "
        "Card given"
    )


# =========================================================
# TRACKERS
# =========================================================

def format_year_milestones(
    year: int,
) -> str:
    """Format full-year tracker."""

    milestones = get_milestones_for_year(
        year
    )

    if not milestones:

        return (
            f"🏆 {year} MILESTONE TRACKER\n\n"
            "No milestones have been added yet."
        )

    lines = [
        f"🏆 {year} MILESTONE TRACKER",
        "",
        f"Total known milestones: {len(milestones)}",
        "",
    ]

    current_month = None

    for milestone in milestones:

        if milestone.milestone_month != current_month:

            current_month = milestone.milestone_month

            lines.extend(
                [
                    "",
                    f"📅 {month_name[current_month].upper()}",
                ]
            )

        emoji = get_milestone_type_emoji(
            milestone.milestone_type
        )

        label = get_milestone_type_label(
            milestone.milestone_type
        )

        status = (
            "✅"
            if is_milestone_complete(
                milestone
            )
            else "⬜"
        )

        lines.append(
            (
                f"{status} #{milestone.id} "
                f"{milestone.person_name} — "
                f"{emoji} {label}"
            )
        )

    return "\n".join(
        lines
    )


def format_month_milestones(
    year: int,
    month: int,
) -> str:
    """Format monthly celebrations."""

    milestones = get_milestones_for_month(
        year,
        month,
    )

    if not milestones:

        return (
            f"🏆 {month_name[month].upper()} "
            f"{year} MILESTONES\n\n"
            "No milestones are currently recorded "
            "for this month."
        )

    lines = [
        f"🏆 {month_name[month].upper()} "
        f"{year} MILESTONES",
        "",
        "Milestones to celebrate this month:",
        "",
    ]

    for milestone in milestones:

        emoji = get_milestone_type_emoji(
            milestone.milestone_type
        )

        label = get_milestone_type_label(
            milestone.milestone_type
        )

        lines.extend(
            [
                (
                    f"{emoji} #{milestone.id} "
                    f"{milestone.person_name}"
                ),
                label,
                f"📅 {format_milestone_date(milestone)}",
                (
                    f"🎁 Gift prepared: "
                    f"{'✅' if milestone.gift_prepared else '⬜'}"
                ),
                (
                    f"💌 Card prepared: "
                    f"{'✅' if milestone.card_prepared else '⬜'}"
                ),
                "",
            ]
        )

    lines.append(
        "Please make sure every milestone this month "
        "is prepared for and celebrated."
    )

    return "\n".join(
        lines
    )


def format_active_milestones() -> str:
    """Format unfinished milestones."""

    milestones = get_active_milestones()

    if not milestones:

        return (
            "🏆 ACTIVE MILESTONES\n\n"
            "No outstanding milestones."
        )

    lines = [
        "🏆 ACTIVE MILESTONES",
        "",
    ]

    for milestone in milestones:

        emoji = get_milestone_type_emoji(
            milestone.milestone_type
        )

        label = get_milestone_type_label(
            milestone.milestone_type
        )

        lines.append(
            (
                f"#{milestone.id} "
                f"{milestone.person_name} — "
                f"{emoji} {label} — "
                f"{format_milestone_date(milestone)}"
            )
        )

    return "\n".join(
        lines
    )


def format_milestone_history(
    year: int,
) -> str:
    """Format completed milestone history."""

    milestones = get_completed_milestones(
        year
    )

    if not milestones:

        return (
            f"📚 {year} MILESTONE HISTORY\n\n"
            "No completed milestones yet."
        )

    lines = [
        f"📚 {year} MILESTONE HISTORY",
        "",
    ]

    for milestone in milestones:

        emoji = get_milestone_type_emoji(
            milestone.milestone_type
        )

        label = get_milestone_type_label(
            milestone.milestone_type
        )

        lines.append(
            (
                f"✅ #{milestone.id} "
                f"{milestone.person_name} — "
                f"{emoji} {label} — "
                f"{format_milestone_date(milestone)}"
            )
        )

    return "\n".join(
        lines
    )


# =========================================================
# INDIVIDUAL REMINDER TEXT
# =========================================================

def build_one_month_reminder(
    milestone: CareMilestone,
) -> str:
    """Build one-month preparation reminder."""

    emoji = get_milestone_type_emoji(
        milestone.milestone_type
    )

    label = get_milestone_type_label(
        milestone.milestone_type
    )

    return (
        "🏆 MILESTONE COMING UP IN 1 MONTH\n\n"
        f"👤 {milestone.person_name}\n"
        f"{emoji} {label}\n"
        f"📅 {format_milestone_date(milestone)}\n\n"
        "CARE preparation:\n\n"
        f"{'✅' if milestone.gift_prepared else '⬜'} "
        "Gift prepared\n"
        f"{'✅' if milestone.card_prepared else '⬜'} "
        "Card prepared\n\n"
        "Please start preparing the gift and card."
    )


def build_two_week_reminder(
    milestone: CareMilestone,
) -> str:
    """Build two-week progress reminder."""

    emoji = get_milestone_type_emoji(
        milestone.milestone_type
    )

    label = get_milestone_type_label(
        milestone.milestone_type
    )

    outstanding = []

    if not milestone.gift_prepared:
        outstanding.append(
            "⬜ Gift prepared"
        )

    if not milestone.card_prepared:
        outstanding.append(
            "⬜ Card prepared"
        )

    if not outstanding:
        outstanding.append(
            "✅ Gift and card are prepared"
        )

    return (
        "⏰ MILESTONE IN 2 WEEKS\n\n"
        f"👤 {milestone.person_name}\n"
        f"{emoji} {label}\n"
        f"📅 {format_milestone_date(milestone)}\n\n"
        "Current preparation:\n\n"
        + "\n".join(
            outstanding
        )
        + "\n\nPlease make sure everything is ready "
        "before the milestone."
    )


# =========================================================
# ANNUAL PLAN
# =========================================================

def get_or_create_milestone_annual_plan(
    target_year: int,
) -> CareMilestoneAnnualPlan:
    """Get or create annual plan."""

    if target_year < 2000:
        raise ValueError(
            "Invalid target year."
        )

    with SessionLocal() as session:

        plan = session.scalar(
            select(
                CareMilestoneAnnualPlan
            ).where(
                CareMilestoneAnnualPlan.target_year
                == target_year
            )
        )

        if plan is None:

            plan = CareMilestoneAnnualPlan(
                target_year=target_year,
            )

            session.add(
                plan
            )

            session.commit()
            session.refresh(
                plan
            )

        return plan


def set_milestone_gift(
    target_year: int,
    milestone_type: str,
    gift_description: str,
) -> CareMilestoneAnnualPlan:
    """Set annual gift choice."""

    type_key = normalise_milestone_type(
        milestone_type
    )

    field_name = ANNUAL_GIFT_FIELDS[
        type_key
    ]

    cleaned_description = gift_description.strip()

    if not cleaned_description:
        raise ValueError(
            "Gift description cannot be empty."
        )

    with SessionLocal() as session:

        plan = session.scalar(
            select(
                CareMilestoneAnnualPlan
            ).where(
                CareMilestoneAnnualPlan.target_year
                == target_year
            )
        )

        if plan is None:

            plan = CareMilestoneAnnualPlan(
                target_year=target_year,
            )

            session.add(
                plan
            )

            session.flush()

        setattr(
            plan,
            field_name,
            cleaned_description,
        )

        plan.updated_at = datetime.now()

        session.commit()
        session.refresh(
            plan
        )

        return plan


def toggle_milestone_lookout_item(
    target_year: int,
    item_key: str,
) -> CareMilestoneAnnualPlan:
    """Toggle annual lookout checklist."""

    fields = {
        "leaders": "cell_leaders_contacted",
        "responses": "responses_collected",
        "entered": "known_milestones_entered",
    }

    field_name = fields.get(
        item_key
    )

    if field_name is None:
        raise ValueError(
            "Unknown lookout checklist item."
        )

    with SessionLocal() as session:

        plan = session.scalar(
            select(
                CareMilestoneAnnualPlan
            ).where(
                CareMilestoneAnnualPlan.target_year
                == target_year
            )
        )

        if plan is None:

            plan = CareMilestoneAnnualPlan(
                target_year=target_year,
            )

            session.add(
                plan
            )

            session.flush()

        current_value = getattr(
            plan,
            field_name,
        )

        setattr(
            plan,
            field_name,
            not current_value,
        )

        plan.updated_at = datetime.now()

        session.commit()
        session.refresh(
            plan
        )

        return plan


def format_milestone_annual_plan(
    target_year: int,
) -> str:
    """Format annual milestone planning."""

    plan = get_or_create_milestone_annual_plan(
        target_year
    )

    gift_lines = []

    for (
        type_key,
        field_name,
    ) in ANNUAL_GIFT_FIELDS.items():

        emoji = get_milestone_type_emoji(
            type_key
        )

        label = get_milestone_type_label(
            type_key
        )

        gift_value = getattr(
            plan,
            field_name,
        )

        gift_lines.append(
            (
                f"{'✅' if gift_value else '⬜'} "
                f"{emoji} {label}: "
                f"{gift_value or 'Not decided'}"
            )
        )

    return (
        f"🏆 {target_year} MILESTONE PLANNING\n\n"
        "👀 MILESTONE LOOKOUT\n"
        f"{'✅' if plan.cell_leaders_contacted else '⬜'} "
        "Cell Leaders contacted\n"
        f"{'✅' if plan.responses_collected else '⬜'} "
        "Responses collected\n"
        f"{'✅' if plan.known_milestones_entered else '⬜'} "
        "Known milestones entered into Dobby\n\n"
        "🎁 GIFT PLANNING\n"
        + "\n".join(
            gift_lines
        )
    )


def build_annual_lookout_reminder(
    target_year: int,
    followup: bool = False,
) -> str:
    """Build November annual lookout reminder."""

    plan = get_or_create_milestone_annual_plan(
        target_year
    )

    if followup:

        outstanding = []

        if not plan.cell_leaders_contacted:
            outstanding.append(
                "⬜ Contact Cell Leaders"
            )

        if not plan.responses_collected:
            outstanding.append(
                "⬜ Collect Cell Leader responses"
            )

        if not plan.known_milestones_entered:
            outstanding.append(
                "⬜ Enter known milestones into Dobby"
            )

        for (
            type_key,
            field_name,
        ) in ANNUAL_GIFT_FIELDS.items():

            if not getattr(
                plan,
                field_name,
            ):

                outstanding.append(
                    (
                        "⬜ Decide "
                        f"{get_milestone_type_label(type_key)} "
                        "gift"
                    )
                )

        if not outstanding:
            outstanding = [
                "✅ Annual milestone planning is complete"
            ]

        return (
            f"🔔 {target_year} MILESTONE PLANNING FOLLOW-UP\n\n"
            + "\n".join(
                outstanding
            )
            + "\n\nPlease settle any outstanding items "
            "before the new year."
        )

    return (
        f"🏆 {target_year} MILESTONE LOOKOUT\n\n"
        "Please check with all Cell Leaders for youths who may be:\n\n"
        "🎓 Graduating Secondary School\n"
        "🎓 Graduating Polytechnic\n"
        "🎓 Graduating JC\n"
        "🎓 Graduating University\n"
        "✝️ Getting Baptised\n"
        "🪖 ORD-ing\n\n"
        "Please add all known milestones into Dobby once confirmed.\n\n"
        "Also decide the standard gift approach for each "
        "milestone category.\n\n"
        + format_milestone_annual_plan(
            target_year
        )
    )


# =========================================================
# ANNUAL REMINDER FLAGS
# =========================================================

def annual_plan_flag_is_set(
    target_year: int,
    field_name: str,
) -> bool:
    """Check annual-plan reminder flag."""

    allowed = {
        "lookout_open_sent",
        "lookout_followup_sent",
        "year_start_tracker_sent",
    }

    if field_name not in allowed:
        raise ValueError(
            "Unknown annual reminder flag."
        )

    plan = get_or_create_milestone_annual_plan(
        target_year
    )

    return bool(
        getattr(
            plan,
            field_name,
        )
    )


def mark_annual_plan_flag(
    target_year: int,
    field_name: str,
) -> None:
    """Mark annual-plan reminder flag."""

    allowed = {
        "lookout_open_sent",
        "lookout_followup_sent",
        "year_start_tracker_sent",
    }

    if field_name not in allowed:
        raise ValueError(
            "Unknown annual reminder flag."
        )

    with SessionLocal() as session:

        plan = session.scalar(
            select(
                CareMilestoneAnnualPlan
            ).where(
                CareMilestoneAnnualPlan.target_year
                == target_year
            )
        )

        if plan is None:

            plan = CareMilestoneAnnualPlan(
                target_year=target_year,
            )

            session.add(
                plan
            )

            session.flush()

        setattr(
            plan,
            field_name,
            True,
        )

        plan.updated_at = datetime.now()

        session.commit()