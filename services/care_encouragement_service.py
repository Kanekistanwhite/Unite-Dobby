from calendar import (
    month_name,
    monthrange,
)
from datetime import (
    date,
    datetime,
)
from zoneinfo import ZoneInfo

from sqlalchemy import (
    func,
    select,
)

from database.database import SessionLocal
from models.care_encouragement_annual_plan import (
    CareEncouragementAnnualPlan,
)
from models.care_encouragement_batch import (
    CareEncouragementBatch,
)
from models.care_encouragement_recipient import (
    CareEncouragementRecipient,
)
from models.care_encouragement_reminder import (
    CareEncouragementReminder,
)


SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


# =========================================================
# BATCH CHECKLIST
# =========================================================

ENCOURAGEMENT_BATCH_CHECKLIST = {
    "recipients": (
        "recipient_list_confirmed",
        "Recipient list confirmed",
    ),
    "cardsready": (
        "cards_ready",
        "Cards ready",
    ),
    "packsready": (
        "packs_ready",
        "Encouragement packs ready",
    ),
    "packingdate": (
        "packing_date_confirmed",
        "Packing date confirmed",
    ),
    "packed": (
        "packs_packed",
        "Packs packed",
    ),
    "cardscompleted": (
        "cards_completed",
        "Cards completed",
    ),
    "distributed": (
        "distribution_completed",
        "Distribution completed",
    ),
}


# =========================================================
# ANNUAL CHECKLIST
# =========================================================

ENCOURAGEMENT_ANNUAL_CHECKLIST = {
    "leaders": (
        "cell_leaders_contacted",
        "Cell Leaders contacted",
    ),
    "exams": (
        "exam_periods_collected",
        "Exam periods collected",
    ),
    "crucial": (
        "crucial_periods_collected",
        "Crucial education periods collected",
    ),
    "entered": (
        "known_periods_entered",
        "Known encouragement periods entered into Dobby",
    ),
    "contents": (
        "contents_decided",
        "Encouragement pack contents decided",
    ),
    "quantity": (
        "quantity_estimated",
        "Estimated quantity confirmed",
    ),
    "items": (
        "items_purchased",
        "Pack contents purchased",
    ),
    "packaging": (
        "packaging_purchased",
        "Packaging / logistics purchased",
    ),
    "cards": (
        "cards_ready",
        "Cards / card materials ready",
    ),
    "stock": (
        "initial_stock_prepared",
        "Initial encouragement stock prepared",
    ),
}


# =========================================================
# TIME
# =========================================================

def get_singapore_today() -> date:
    """Return today's Singapore date."""

    return datetime.now(
        SINGAPORE_TIMEZONE
    ).date()


def get_next_month(
    year: int,
    month: int,
) -> tuple[int, int]:
    """Return the following calendar month."""

    if month == 12:

        return (
            year + 1,
            1,
        )

    return (
        year,
        month + 1,
    )


def get_current_encouragement_plan_year() -> int:
    """Return year currently being planned."""

    return get_singapore_today().year + 1


# =========================================================
# TEXT
# =========================================================

def clean_name(
    value: str,
) -> str:
    """Clean repeated spaces."""

    return " ".join(
        value.strip().split()
    )


# =========================================================
# PERIOD PARSING
# =========================================================

def parse_encouragement_period(
    value: str,
) -> tuple[
    int,
    int,
    date | None,
    date | None,
]:
    """
    Supported:

    MM-YYYY
    DD-MM-YYYY
    DD-MM-YYYY to DD-MM-YYYY
    """

    cleaned = value.strip()

    lowered = cleaned.lower()

    if " to " in lowered:

        start_text, end_text = (
            lowered.split(
                " to ",
                maxsplit=1,
            )
        )

        start_date = datetime.strptime(
            start_text.strip(),
            "%d-%m-%Y",
        ).date()

        end_date = datetime.strptime(
            end_text.strip(),
            "%d-%m-%Y",
        ).date()

        if end_date < start_date:

            raise ValueError(
                "End date cannot be before start date."
            )

        return (
            start_date.year,
            start_date.month,
            start_date,
            end_date,
        )

    parts = cleaned.split(
        "-"
    )

    if len(parts) == 3:

        exact_date = datetime.strptime(
            cleaned,
            "%d-%m-%Y",
        ).date()

        return (
            exact_date.year,
            exact_date.month,
            exact_date,
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
            None,
        )

    raise ValueError(
        "Period must be MM-YYYY, DD-MM-YYYY, "
        "or DD-MM-YYYY to DD-MM-YYYY."
    )


def parse_exact_date(
    value: str,
) -> date:
    """Parse DD-MM-YYYY."""

    try:

        return datetime.strptime(
            value.strip(),
            "%d-%m-%Y",
        ).date()

    except ValueError as error:

        raise ValueError(
            "Date must be DD-MM-YYYY."
        ) from error


# =========================================================
# BATCHES
# =========================================================

def add_encouragement_batch(
    title: str,
    period: str,
) -> CareEncouragementBatch:
    """Create encouragement batch."""

    cleaned_title = clean_name(
        title
    )

    if not cleaned_title:

        raise ValueError(
            "Encouragement title is required."
        )

    (
        year,
        month,
        start_date,
        end_date,
    ) = parse_encouragement_period(
        period
    )

    with SessionLocal() as session:

        batch = CareEncouragementBatch(
            title=cleaned_title,
            encouragement_year=year,
            encouragement_month=month,
            start_date=start_date,
            end_date=end_date,
        )

        session.add(
            batch
        )

        session.commit()
        session.refresh(
            batch
        )

        return batch


def get_encouragement_batch(
    batch_id: int,
) -> CareEncouragementBatch | None:
    """Get one batch."""

    with SessionLocal() as session:

        return session.get(
            CareEncouragementBatch,
            batch_id,
        )


def get_active_encouragement_batches(
) -> list[CareEncouragementBatch]:
    """Return unfinished batches."""

    with SessionLocal() as session:

        batches = session.scalars(
            select(
                CareEncouragementBatch
            )
            .where(
                CareEncouragementBatch.is_cancelled.is_(
                    False
                ),
                CareEncouragementBatch.distribution_completed.is_(
                    False
                ),
            )
            .order_by(
                CareEncouragementBatch.encouragement_year,
                CareEncouragementBatch.encouragement_month,
                CareEncouragementBatch.start_date,
                CareEncouragementBatch.id,
            )
        ).all()

        return list(
            batches
        )


def get_encouragement_batches_for_month(
    year: int,
    month: int,
) -> list[CareEncouragementBatch]:
    """
    Return encouragement periods overlapping a month.

    A date range that spans two months will appear
    in both relevant monthly views.
    """

    month_start = date(
        year,
        month,
        1,
    )

    month_end = date(
        year,
        month,
        monthrange(
            year,
            month,
        )[1],
    )

    with SessionLocal() as session:

        batches = session.scalars(
            select(
                CareEncouragementBatch
            )
            .where(
                CareEncouragementBatch.is_cancelled.is_(
                    False
                ),
            )
            .order_by(
                CareEncouragementBatch.encouragement_year,
                CareEncouragementBatch.encouragement_month,
                CareEncouragementBatch.start_date,
                CareEncouragementBatch.id,
            )
        ).all()

        results = []

        for batch in batches:

            if (
                batch.start_date is not None
                and batch.end_date is not None
            ):

                overlaps = (
                    batch.start_date <= month_end
                    and batch.end_date >= month_start
                )

                if overlaps:

                    results.append(
                        batch
                    )

                continue

            if (
                batch.encouragement_year == year
                and batch.encouragement_month == month
            ):

                results.append(
                    batch
                )

        return results


# =========================================================
# RECIPIENTS
# =========================================================

def get_batch_recipients(
    batch_id: int,
) -> list[CareEncouragementRecipient]:
    """Return recipients."""

    with SessionLocal() as session:

        recipients = session.scalars(
            select(
                CareEncouragementRecipient
            )
            .where(
                CareEncouragementRecipient.batch_id
                == batch_id
            )
            .order_by(
                CareEncouragementRecipient.person_name
            )
        ).all()

        return list(
            recipients
        )


def get_encouragement_recipient(
    recipient_id: int,
) -> CareEncouragementRecipient | None:
    """Get recipient."""

    with SessionLocal() as session:

        return session.get(
            CareEncouragementRecipient,
            recipient_id,
        )


def add_encouragement_recipient(
    batch_id: int,
    person_name: str,
) -> CareEncouragementRecipient:
    """Add youth to batch."""

    cleaned_name = clean_name(
        person_name
    )

    if not cleaned_name:

        raise ValueError(
            "Recipient name is required."
        )

    with SessionLocal() as session:

        batch = session.get(
            CareEncouragementBatch,
            batch_id,
        )

        if batch is None:

            raise ValueError(
                "Encouragement batch not found."
            )

        if batch.is_cancelled:

            raise ValueError(
                "This encouragement batch is cancelled."
            )

        existing = session.scalar(
            select(
                CareEncouragementRecipient
            ).where(
                CareEncouragementRecipient.batch_id
                == batch_id,
                func.lower(
                    CareEncouragementRecipient.person_name
                )
                == cleaned_name.lower(),
            )
        )

        if existing is not None:

            raise ValueError(
                f"{existing.person_name} is already "
                "in this encouragement batch."
            )

        recipient = CareEncouragementRecipient(
            batch_id=batch_id,
            person_name=cleaned_name,
        )

        session.add(
            recipient
        )

        batch.distribution_completed = False
        batch.updated_at = datetime.now()

        session.commit()
        session.refresh(
            recipient
        )

        return recipient


def refresh_distribution_status(
    session,
    batch_id: int,
) -> None:
    """Refresh overall distribution status."""

    batch = session.get(
        CareEncouragementBatch,
        batch_id,
    )

    if batch is None:
        return

    recipients = session.scalars(
        select(
            CareEncouragementRecipient
        ).where(
            CareEncouragementRecipient.batch_id
            == batch_id
        )
    ).all()

    if not recipients:

        batch.distribution_completed = False
        batch.updated_at = datetime.now()

        return

    batch.distribution_completed = all(
        recipient.card_given
        and recipient.pack_given
        for recipient in recipients
    )

    batch.updated_at = datetime.now()


def remove_encouragement_recipient(
    recipient_id: int,
) -> tuple[
    bool,
    str | None,
]:
    """Remove one recipient."""

    with SessionLocal() as session:

        recipient = session.get(
            CareEncouragementRecipient,
            recipient_id,
        )

        if recipient is None:

            return (
                False,
                None,
            )

        name = recipient.person_name
        batch_id = recipient.batch_id

        session.delete(
            recipient
        )

        session.flush()

        refresh_distribution_status(
            session,
            batch_id,
        )

        session.commit()

        return (
            True,
            name,
        )


def toggle_recipient_item(
    recipient_id: int,
    item_key: str,
) -> CareEncouragementRecipient:
    """Toggle card/pack given."""

    fields = {
        "card": "card_given",
        "pack": "pack_given",
    }

    field_name = fields.get(
        item_key
    )

    if field_name is None:

        raise ValueError(
            "Unknown recipient checklist item."
        )

    with SessionLocal() as session:

        recipient = session.get(
            CareEncouragementRecipient,
            recipient_id,
        )

        if recipient is None:

            raise ValueError(
                "Recipient not found."
            )

        current_value = getattr(
            recipient,
            field_name,
        )

        setattr(
            recipient,
            field_name,
            not current_value,
        )

        session.flush()

        refresh_distribution_status(
            session,
            recipient.batch_id,
        )

        session.commit()
        session.refresh(
            recipient
        )

        return recipient


# =========================================================
# PACKING DATE
# =========================================================

def set_encouragement_packing_date(
    batch_id: int,
    packing_date_text: str,
) -> CareEncouragementBatch:
    """Set packing session date."""

    packing_date = parse_exact_date(
        packing_date_text
    )

    with SessionLocal() as session:

        batch = session.get(
            CareEncouragementBatch,
            batch_id,
        )

        if batch is None:

            raise ValueError(
                "Encouragement batch not found."
            )

        batch.packing_date = packing_date
        batch.packing_date_confirmed = True
        batch.updated_at = datetime.now()

        session.commit()
        session.refresh(
            batch
        )

        return batch


# =========================================================
# BATCH CHECKLIST
# =========================================================

def toggle_encouragement_batch_item(
    batch_id: int,
    item_key: str,
) -> CareEncouragementBatch:
    """Toggle batch checklist item."""

    item = ENCOURAGEMENT_BATCH_CHECKLIST.get(
        item_key
    )

    if item is None:

        raise ValueError(
            "Unknown encouragement checklist item."
        )

    field_name = item[0]

    with SessionLocal() as session:

        batch = session.get(
            CareEncouragementBatch,
            batch_id,
        )

        if batch is None:

            raise ValueError(
                "Encouragement batch not found."
            )

        setattr(
            batch,
            field_name,
            not getattr(
                batch,
                field_name,
            ),
        )

        batch.updated_at = datetime.now()

        session.commit()
        session.refresh(
            batch
        )

        return batch


# =========================================================
# CANCEL
# =========================================================

def cancel_encouragement_batch(
    batch_id: int,
) -> bool:
    """Cancel batch."""

    with SessionLocal() as session:

        batch = session.get(
            CareEncouragementBatch,
            batch_id,
        )

        if batch is None:
            return False

        batch.is_cancelled = True
        batch.updated_at = datetime.now()

        session.commit()

        return True


# =========================================================
# FORMATTING
# =========================================================

def format_encouragement_period(
    batch: CareEncouragementBatch,
) -> str:
    """Format period."""

    if (
        batch.start_date is None
        and batch.end_date is None
    ):

        return (
            f"{month_name[batch.encouragement_month]} "
            f"{batch.encouragement_year}"
        )

    if (
        batch.start_date is not None
        and batch.end_date is not None
        and batch.start_date == batch.end_date
    ):

        return batch.start_date.strftime(
            "%d %b %Y"
        )

    if (
        batch.start_date is not None
        and batch.end_date is not None
    ):

        return (
            f"{batch.start_date.strftime('%d %b %Y')} "
            f"to "
            f"{batch.end_date.strftime('%d %b %Y')}"
        )

    return (
        f"{month_name[batch.encouragement_month]} "
        f"{batch.encouragement_year}"
    )


def format_encouragement_batch(
    batch: CareEncouragementBatch,
) -> str:
    """Format batch."""

    recipients = get_batch_recipients(
        batch.id
    )

    started = (
        bool(recipients)
        or batch.recipient_list_confirmed
        or batch.cards_ready
        or batch.packs_ready
        or batch.packing_date_confirmed
        or batch.packs_packed
        or batch.cards_completed
    )

    if batch.distribution_completed:

        status = "✅ COMPLETED"

    elif (
        batch.packs_packed
        or batch.cards_completed
    ):

        status = "🟠 DISTRIBUTION PENDING"

    elif started:

        status = "🟡 PREPARING"

    else:

        status = "⚪ NOT STARTED"

    packing_date = (
        batch.packing_date.strftime(
            "%d %b %Y"
        )
        if batch.packing_date
        else "Not set"
    )

    return (
        f"💌 ENCOURAGEMENT BATCH #{batch.id}\n\n"
        f"📚 {batch.title}\n"
        f"📅 Period: "
        f"{format_encouragement_period(batch)}\n"
        f"👥 Recipients: {len(recipients)}\n"
        f"📦 Packing date: {packing_date}\n\n"
        f"{status}\n\n"
        "PREPARATION\n"
        f"{'✅' if batch.recipient_list_confirmed else '⬜'} "
        "Recipient list confirmed\n"
        f"{'✅' if batch.cards_ready else '⬜'} "
        "Cards ready\n"
        f"{'✅' if batch.packs_ready else '⬜'} "
        "Encouragement packs ready\n"
        f"{'✅' if batch.packing_date_confirmed else '⬜'} "
        "Packing date confirmed\n\n"
        "PACKING / FULFILMENT\n"
        f"{'✅' if batch.packs_packed else '⬜'} "
        "Packs packed\n"
        f"{'✅' if batch.cards_completed else '⬜'} "
        "Cards completed\n"
        f"{'✅' if batch.distribution_completed else '⬜'} "
        "Distribution completed"
    )


def format_encouragement_recipient(
    recipient: CareEncouragementRecipient,
) -> str:
    """Format recipient."""

    return (
        f"💌 RECIPIENT #{recipient.id}\n\n"
        f"👤 {recipient.person_name}\n"
        f"📋 Batch #{recipient.batch_id}\n\n"
        f"{'✅' if recipient.card_given else '⬜'} "
        "Card given\n"
        f"{'✅' if recipient.pack_given else '⬜'} "
        "Pack given"
    )


def format_batch_recipients(
    batch_id: int,
) -> str:
    """Format recipient list."""

    batch = get_encouragement_batch(
        batch_id
    )

    if batch is None:

        raise ValueError(
            "Encouragement batch not found."
        )

    recipients = get_batch_recipients(
        batch_id
    )

    if not recipients:

        return (
            f"👥 {batch.title.upper()} RECIPIENTS\n\n"
            "No recipients have been added yet."
        )

    lines = [
        f"👥 {batch.title.upper()} RECIPIENTS",
        "",
        f"Total: {len(recipients)}",
        "",
    ]

    for recipient in recipients:

        complete = (
            recipient.card_given
            and recipient.pack_given
        )

        lines.append(
            (
                f"{'✅' if complete else '⬜'} "
                f"#{recipient.id} "
                f"{recipient.person_name} — "
                f"Card "
                f"{'✅' if recipient.card_given else '⬜'} "
                f"Pack "
                f"{'✅' if recipient.pack_given else '⬜'}"
            )
        )

    return "\n".join(
        lines
    )


def format_active_encouragement_batches() -> str:
    """Format active batches."""

    batches = get_active_encouragement_batches()

    if not batches:

        return (
            "💌 ACTIVE ENCOURAGEMENT BATCHES\n\n"
            "No active encouragement batches."
        )

    lines = [
        "💌 ACTIVE ENCOURAGEMENT BATCHES",
        "",
    ]

    for batch in batches:

        recipients = get_batch_recipients(
            batch.id
        )

        lines.append(
            (
                f"#{batch.id} {batch.title} — "
                f"{format_encouragement_period(batch)} "
                f"— {len(recipients)} recipient(s)"
            )
        )

    return "\n".join(
        lines
    )


def format_encouragement_month(
    year: int,
    month: int,
) -> str:
    """Format encouragement periods overlapping month."""

    batches = get_encouragement_batches_for_month(
        year,
        month,
    )

    if not batches:

        return (
            f"💌 {month_name[month].upper()} "
            f"{year} ENCOURAGEMENT\n\n"
            "No encouragement periods are currently "
            "recorded for this month."
        )

    lines = [
        f"💌 {month_name[month].upper()} "
        f"{year} ENCOURAGEMENT",
        "",
    ]

    for batch in batches:

        recipients = get_batch_recipients(
            batch.id
        )

        lines.extend(
            [
                f"📚 #{batch.id} {batch.title}",
                (
                    f"📅 "
                    f"{format_encouragement_period(batch)}"
                ),
                (
                    f"👥 {len(recipients)} "
                    "recipient(s)"
                ),
                (
                    "📦 Packing: "
                    + (
                        batch.packing_date.strftime(
                            "%d %b %Y"
                        )
                        if batch.packing_date
                        else "Not set"
                    )
                ),
                "",
            ]
        )

    return "\n".join(
        lines
    )


# =========================================================
# ANNUAL PLAN
# =========================================================

def get_or_create_encouragement_annual_plan(
    target_year: int,
) -> CareEncouragementAnnualPlan:
    """Get or create annual plan."""

    if target_year < 2000:

        raise ValueError(
            "Invalid target year."
        )

    with SessionLocal() as session:

        plan = session.scalar(
            select(
                CareEncouragementAnnualPlan
            ).where(
                CareEncouragementAnnualPlan.target_year
                == target_year
            )
        )

        if plan is None:

            plan = CareEncouragementAnnualPlan(
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


def toggle_encouragement_annual_item(
    target_year: int,
    item_key: str,
) -> CareEncouragementAnnualPlan:
    """Toggle annual checklist item."""

    item = ENCOURAGEMENT_ANNUAL_CHECKLIST.get(
        item_key
    )

    if item is None:

        raise ValueError(
            "Unknown annual checklist item."
        )

    field_name = item[0]

    with SessionLocal() as session:

        plan = session.scalar(
            select(
                CareEncouragementAnnualPlan
            ).where(
                CareEncouragementAnnualPlan.target_year
                == target_year
            )
        )

        if plan is None:

            plan = CareEncouragementAnnualPlan(
                target_year=target_year,
            )

            session.add(
                plan
            )

            session.flush()

        setattr(
            plan,
            field_name,
            not getattr(
                plan,
                field_name,
            ),
        )

        plan.updated_at = datetime.now()

        session.commit()
        session.refresh(
            plan
        )

        return plan


def get_incomplete_encouragement_annual_items(
    plan: CareEncouragementAnnualPlan,
) -> list[str]:
    """Return unfinished annual items."""

    incomplete = []

    for (
        field_name,
        label,
    ) in ENCOURAGEMENT_ANNUAL_CHECKLIST.values():

        if not getattr(
            plan,
            field_name,
        ):

            incomplete.append(
                label
            )

    return incomplete


def format_encouragement_annual_plan(
    target_year: int,
) -> str:
    """Format annual Encouragement planning."""

    plan = get_or_create_encouragement_annual_plan(
        target_year
    )

    completed = 0

    lines = [
        f"💌 {target_year} ENCOURAGEMENT PREPARATION",
        "",
        "👀 EXAM / CRUCIAL PERIOD LOOKOUT",
    ]

    lookout_keys = (
        "leaders",
        "exams",
        "crucial",
        "entered",
    )

    for item_key in lookout_keys:

        field_name, label = (
            ENCOURAGEMENT_ANNUAL_CHECKLIST[
                item_key
            ]
        )

        done = getattr(
            plan,
            field_name,
        )

        if done:
            completed += 1

        lines.append(
            f"{'✅' if done else '⬜'} {label}"
        )

    lines.extend(
        [
            "",
            "🎁 CARE PACK PLANNING",
        ]
    )

    prep_keys = (
        "contents",
        "quantity",
        "items",
        "packaging",
        "cards",
        "stock",
    )

    for item_key in prep_keys:

        field_name, label = (
            ENCOURAGEMENT_ANNUAL_CHECKLIST[
                item_key
            ]
        )

        done = getattr(
            plan,
            field_name,
        )

        if done:
            completed += 1

        lines.append(
            f"{'✅' if done else '⬜'} {label}"
        )

    total = len(
        ENCOURAGEMENT_ANNUAL_CHECKLIST
    )

    if completed == total:

        status = "✅ COMPLETED"

    elif completed == 0:

        status = "⚪ NOT STARTED"

    else:

        status = "🟡 IN PROGRESS"

    lines.extend(
        [
            "",
            status,
            f"Progress: {completed} / {total}",
        ]
    )

    return "\n".join(
        lines
    )


def build_encouragement_annual_reminder(
    target_year: int,
    followup: bool = False,
) -> str:
    """Build November annual reminder."""

    plan = get_or_create_encouragement_annual_plan(
        target_year
    )

    if followup:

        incomplete = (
            get_incomplete_encouragement_annual_items(
                plan
            )
        )

        if not incomplete:

            incomplete_text = (
                "✅ Annual Encouragement preparation "
                "is complete."
            )

        else:

            incomplete_text = "\n".join(
                f"⬜ {item}"
                for item in incomplete
            )

        return (
            f"🔔 {target_year} ENCOURAGEMENT "
            "PLANNING FOLLOW-UP\n\n"
            f"{incomplete_text}\n\n"
            "Please follow up any outstanding "
            "Cell Leaders, exam periods and pack preparation."
        )

    return (
        f"💌 {target_year} ENCOURAGEMENT PREPARATION\n\n"
        "Please check with Cell Leaders for the major "
        "education periods their youths will face next year.\n\n"
        "Examples:\n"
        "📚 Mid-Year Exams\n"
        "📚 Preliminary Exams\n"
        "📚 N / O / A Levels\n"
        "📚 Polytechnic Exams\n"
        "📚 University Exams\n"
        "📚 Other crucial education periods\n\n"
        "Also begin planning next year's encouragement packs.\n\n"
        + format_encouragement_annual_plan(
            target_year
        )
    )


def annual_encouragement_flag_is_set(
    target_year: int,
    field_name: str,
) -> bool:
    """Check annual reminder flag."""

    allowed = {
        "lookout_open_sent",
        "lookout_followup_sent",
    }

    if field_name not in allowed:

        raise ValueError(
            "Unknown annual reminder flag."
        )

    plan = get_or_create_encouragement_annual_plan(
        target_year
    )

    return bool(
        getattr(
            plan,
            field_name,
        )
    )


def mark_annual_encouragement_flag(
    target_year: int,
    field_name: str,
) -> None:
    """Mark annual reminder flag."""

    allowed = {
        "lookout_open_sent",
        "lookout_followup_sent",
    }

    if field_name not in allowed:

        raise ValueError(
            "Unknown annual reminder flag."
        )

    with SessionLocal() as session:

        plan = session.scalar(
            select(
                CareEncouragementAnnualPlan
            ).where(
                CareEncouragementAnnualPlan.target_year
                == target_year
            )
        )

        if plan is None:

            plan = CareEncouragementAnnualPlan(
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


# =========================================================
# REMINDER HISTORY
# =========================================================

def encouragement_reminder_was_sent(
    year: int,
    month: int,
    reminder_type: str,
) -> bool:
    """Check reminder history."""

    with SessionLocal() as session:

        reminder = session.scalar(
            select(
                CareEncouragementReminder
            ).where(
                CareEncouragementReminder.year
                == year,
                CareEncouragementReminder.month
                == month,
                CareEncouragementReminder.reminder_type
                == reminder_type,
            )
        )

        return reminder is not None


def record_encouragement_reminder_sent(
    year: int,
    month: int,
    reminder_type: str,
) -> None:
    """Record reminder."""

    with SessionLocal() as session:

        existing = session.scalar(
            select(
                CareEncouragementReminder
            ).where(
                CareEncouragementReminder.year
                == year,
                CareEncouragementReminder.month
                == month,
                CareEncouragementReminder.reminder_type
                == reminder_type,
            )
        )

        if existing is not None:
            return

        session.add(
            CareEncouragementReminder(
                year=year,
                month=month,
                reminder_type=reminder_type,
                sent_at=datetime.now(),
            )
        )

        session.commit()


# =========================================================
# MONTHLY LOOKAHEAD
# =========================================================

def build_monthly_encouragement_lookahead(
    year: int,
    month: int,
) -> str:
    """Build one-month-ahead preparation reminder."""

    batches = get_encouragement_batches_for_month(
        year,
        month,
    )

    heading = (
        f"💌 {month_name[month].upper()} "
        "ENCOURAGEMENT LOOKAHEAD"
    )

    if not batches:

        return (
            f"{heading}\n\n"
            "No encouragement periods are currently "
            "recorded for this month.\n\n"
            "👀 Please check whether any youths have "
            "upcoming exams or other crucial education "
            "periods that need encouragement."
        )

    lines = [
        heading,
        "",
        (
            f"{len(batches)} encouragement "
            f"batch{'es' if len(batches) != 1 else ''} "
            "currently recorded."
        ),
        "",
    ]

    for batch in batches:

        recipients = get_batch_recipients(
            batch.id
        )

        lines.extend(
            [
                f"📚 #{batch.id} {batch.title}",
                (
                    f"📅 "
                    f"{format_encouragement_period(batch)}"
                ),
                "",
                "👥 Recipients:",
            ]
        )

        if recipients:

            for recipient in recipients:

                lines.append(
                    f"• {recipient.person_name}"
                )

        else:

            lines.append(
                "• No recipients added yet"
            )

        lines.extend(
            [
                "",
                "Preparation:",
                (
                    f"{'✅' if batch.recipient_list_confirmed else '⬜'} "
                    "Recipient list confirmed"
                ),
                (
                    f"{'✅' if batch.cards_ready else '⬜'} "
                    "Cards ready"
                ),
                (
                    f"{'✅' if batch.packs_ready else '⬜'} "
                    "Encouragement packs ready"
                ),
                (
                    f"{'✅' if batch.packing_date_confirmed else '⬜'} "
                    "Packing date confirmed"
                ),
                (
                    "📦 Packing date: "
                    + (
                        batch.packing_date.strftime(
                            "%d %b %Y"
                        )
                        if batch.packing_date
                        else "Not set"
                    )
                ),
                "",
            ]
        )

    lines.append(
        "Please begin preparing the packs and cards "
        "for these youths."
    )

    return "\n".join(
        lines
    )


# =========================================================
# PACKING REMINDER
# =========================================================

def build_encouragement_packing_reminder(
    batch: CareEncouragementBatch,
    one_day: bool = False,
) -> str:
    """Build packing-session reminder."""

    recipients = get_batch_recipients(
        batch.id
    )

    if one_day:

        heading = (
            "🚨 ENCOURAGEMENT PACKING TOMORROW"
        )

    else:

        heading = (
            "📦 ENCOURAGEMENT PACKING IN 1 WEEK"
        )

    lines = [
        heading,
        "",
        f"📚 {batch.title}",
        (
            f"📅 Encouragement period: "
            f"{format_encouragement_period(batch)}"
        ),
        (
            "📦 Packing date: "
            + (
                batch.packing_date.strftime(
                    "%d %b %Y"
                )
                if batch.packing_date
                else "Not set"
            )
        ),
        "",
        f"👥 Recipients: {len(recipients)}",
    ]

    if recipients:

        for recipient in recipients:

            lines.append(
                f"• {recipient.person_name}"
            )

    lines.extend(
        [
            "",
            "Current preparation:",
            (
                f"{'✅' if batch.recipient_list_confirmed else '⬜'} "
                "Recipient list confirmed"
            ),
            (
                f"{'✅' if batch.cards_ready else '⬜'} "
                "Cards ready"
            ),
            (
                f"{'✅' if batch.packs_ready else '⬜'} "
                "Pack contents ready"
            ),
            "",
            (
                "Please make sure everything needed "
                "for the packing session is ready."
            ),
        ]
    )

    return "\n".join(
        lines
    )