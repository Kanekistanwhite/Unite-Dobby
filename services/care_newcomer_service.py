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
from models.care_newcomer import CareNewcomer
from models.care_newcomer_annual_prep import (
    CareNewcomerAnnualPrep,
)
from models.care_newcomer_inventory import (
    CareNewcomerInventory,
)


SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


# =========================================================
# ANNUAL PREP CHECKLIST
# =========================================================

NEWCOMER_ANNUAL_PREP_CHECKLIST = {
    "contents": (
        "contents_confirmed",
        "Newcomer pack contents confirmed",
    ),
    "quantity": (
        "quantity_confirmed",
        "Quantity of 50 packs confirmed",
    ),
    "items": (
        "items_purchased",
        "Snacks / pack items purchased",
    ),
    "packaging": (
        "packaging_purchased",
        "Packaging / logistics purchased",
    ),
    "arrived": (
        "all_items_arrived",
        "All items received",
    ),
    "packed": (
        "packs_packed",
        "50 newcomer packs packed",
    ),
    "stock": (
        "final_stock_confirmed",
        "Final stock count confirmed",
    ),
}


# =========================================================
# TIME
# =========================================================

def get_singapore_now() -> datetime:
    """Return current Singapore time."""

    return datetime.now(
        SINGAPORE_TIMEZONE
    ).replace(
        tzinfo=None
    )


def get_singapore_today() -> date:
    """Return today's Singapore date."""

    return datetime.now(
        SINGAPORE_TIMEZONE
    ).date()


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_name(
    value: str,
) -> str:
    """Clean repeated spaces from a person's name."""

    return " ".join(
        value.strip().split()
    )


# =========================================================
# INVENTORY
# =========================================================

def get_or_create_newcomer_inventory(
    year: int,
) -> CareNewcomerInventory:
    """Get or create newcomer-pack inventory for a year."""

    if year < 2000:
        raise ValueError(
            "Invalid year."
        )

    with SessionLocal() as session:

        inventory = session.scalar(
            select(
                CareNewcomerInventory
            ).where(
                CareNewcomerInventory.year
                == year
            )
        )

        if inventory is None:

            inventory = (
                CareNewcomerInventory(
                    year=year,
                    starting_stock=50,
                    current_stock=50,
                    packs_given=0,
                    replenished_stock=0,
                    low_stock_threshold=10,
                )
            )

            session.add(
                inventory
            )

            session.commit()
            session.refresh(
                inventory
            )

        return inventory


def set_newcomer_stock(
    year: int,
    quantity: int,
) -> CareNewcomerInventory:
    """Set current physical newcomer-pack stock."""

    if quantity < 0:
        raise ValueError(
            "Stock cannot be negative."
        )

    with SessionLocal() as session:

        inventory = session.scalar(
            select(
                CareNewcomerInventory
            ).where(
                CareNewcomerInventory.year
                == year
            )
        )

        if inventory is None:

            inventory = (
                CareNewcomerInventory(
                    year=year,
                    starting_stock=quantity,
                    current_stock=quantity,
                    packs_given=0,
                    replenished_stock=0,
                )
            )

            session.add(
                inventory
            )

        else:
            inventory.current_stock = quantity

        inventory.stock_quantity_updated = True
        inventory.updated_at = datetime.now()

        session.commit()
        session.refresh(
            inventory
        )

        return inventory


def add_newcomer_stock(
    year: int,
    quantity: int,
) -> CareNewcomerInventory:
    """Add replenished newcomer packs."""

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    with SessionLocal() as session:

        inventory = session.scalar(
            select(
                CareNewcomerInventory
            ).where(
                CareNewcomerInventory.year
                == year
            )
        )

        if inventory is None:

            inventory = (
                CareNewcomerInventory(
                    year=year,
                    starting_stock=50,
                    current_stock=50,
                    packs_given=0,
                    replenished_stock=0,
                )
            )

            session.add(
                inventory
            )

            session.flush()

        inventory.current_stock += quantity
        inventory.replenished_stock += quantity
        inventory.stock_quantity_updated = True
        inventory.updated_at = datetime.now()

        session.commit()
        session.refresh(
            inventory
        )

        return inventory


def format_newcomer_inventory(
    year: int,
) -> str:
    """Format yearly newcomer-pack stock."""

    inventory = get_or_create_newcomer_inventory(
        year
    )

    total_available = (
        inventory.starting_stock
        + inventory.replenished_stock
    )

    lines = [
        f"📦 NEWCOMER PACK INVENTORY — {year}",
        "",
        f"Starting stock: {inventory.starting_stock}",
        (
            "Additional packs prepared: "
            f"{inventory.replenished_stock}"
        ),
        f"Total available: {total_available}",
        f"Packs given: {inventory.packs_given}",
        f"Remaining: {inventory.current_stock}",
    ]

    if (
        inventory.current_stock
        <= inventory.low_stock_threshold
    ):

        lines.extend(
            [
                "",
                "⚠️ LOW STOCK",
                (
                    f"Only {inventory.current_stock} "
                    "newcomer pack(s) remaining."
                ),
                "Please consider replenishing the stock.",
            ]
        )

    return "\n".join(
        lines
    )


# =========================================================
# NEWCOMER LOOKUP
# =========================================================

def find_newcomer(
    display_name: str,
) -> CareNewcomer | None:
    """Find newcomer by case-insensitive exact name."""

    cleaned_name = clean_name(
        display_name
    )

    if not cleaned_name:
        return None

    with SessionLocal() as session:

        newcomer = session.scalar(
            select(
                CareNewcomer
            )
            .where(
                func.lower(
                    CareNewcomer.display_name
                )
                == cleaned_name.lower()
            )
            .order_by(
                CareNewcomer.first_visit_date
            )
        )

        return newcomer


def get_recent_newcomers(
    limit: int = 20,
) -> list[CareNewcomer]:
    """Return recently registered newcomers."""

    with SessionLocal() as session:

        newcomers = session.scalars(
            select(
                CareNewcomer
            )
            .order_by(
                CareNewcomer.first_visit_date.desc(),
                CareNewcomer.id.desc(),
            )
            .limit(
                limit
            )
        ).all()

        return list(
            newcomers
        )


def get_newcomer_count() -> int:
    """Return total people in newcomer register."""

    with SessionLocal() as session:

        newcomers = session.scalars(
            select(
                CareNewcomer
            )
        ).all()

        return len(
            newcomers
        )


# =========================================================
# REGISTER NEWCOMER
# =========================================================

def register_newcomer(
    display_name: str,
    invited_by: str,
    first_visit_date: date | None = None,
) -> tuple[
    str,
    CareNewcomer,
    CareNewcomerInventory,
]:
    """Register a newcomer."""

    cleaned_name = clean_name(
        display_name
    )

    cleaned_invited_by = clean_name(
        invited_by
    )

    if not cleaned_name:
        raise ValueError(
            "Newcomer name is required."
        )

    if not cleaned_invited_by:
        raise ValueError(
            "Invited-by name is required."
        )

    if first_visit_date is None:
        first_visit_date = (
            get_singapore_today()
        )

    existing = find_newcomer(
        cleaned_name
    )

    if existing is not None:

        inventory = (
            get_or_create_newcomer_inventory(
                get_singapore_today().year
            )
        )

        return (
            "duplicate",
            existing,
            inventory,
        )

    inventory_year = (
        first_visit_date.year
    )

    with SessionLocal() as session:

        inventory = session.scalar(
            select(
                CareNewcomerInventory
            ).where(
                CareNewcomerInventory.year
                == inventory_year
            )
        )

        if inventory is None:

            inventory = (
                CareNewcomerInventory(
                    year=inventory_year,
                    starting_stock=50,
                    current_stock=50,
                    packs_given=0,
                    replenished_stock=0,
                    low_stock_threshold=10,
                )
            )

            session.add(
                inventory
            )

            session.flush()

        pack_given = (
            inventory.current_stock > 0
        )

        newcomer = CareNewcomer(
            display_name=cleaned_name,
            invited_by=cleaned_invited_by,
            first_visit_date=first_visit_date,
            pack_given=pack_given,
        )

        session.add(
            newcomer
        )

        if pack_given:
            inventory.current_stock -= 1
            inventory.packs_given += 1

        inventory.updated_at = datetime.now()

        session.commit()

        session.refresh(
            newcomer
        )

        session.refresh(
            inventory
        )

        status = (
            "registered"
            if pack_given
            else "registered_no_pack"
        )

        return (
            status,
            newcomer,
            inventory,
        )


# =========================================================
# GIVE PACK LATER
# =========================================================

def give_pack_to_newcomer(
    display_name: str,
) -> tuple[
    str,
    CareNewcomer | None,
    CareNewcomerInventory,
]:
    """Give pack to a registered newcomer later."""

    newcomer = find_newcomer(
        display_name
    )

    current_year = (
        get_singapore_today().year
    )

    inventory = (
        get_or_create_newcomer_inventory(
            current_year
        )
    )

    if newcomer is None:

        return (
            "not_found",
            None,
            inventory,
        )

    if newcomer.pack_given:

        return (
            "already_given",
            newcomer,
            inventory,
        )

    if inventory.current_stock <= 0:

        return (
            "no_stock",
            newcomer,
            inventory,
        )

    with SessionLocal() as session:

        stored_newcomer = session.get(
            CareNewcomer,
            newcomer.id,
        )

        stored_inventory = session.scalar(
            select(
                CareNewcomerInventory
            ).where(
                CareNewcomerInventory.year
                == current_year
            )
        )

        if (
            stored_newcomer is None
            or stored_inventory is None
        ):
            raise RuntimeError(
                "Newcomer or inventory could not be loaded."
            )

        stored_newcomer.pack_given = True

        stored_inventory.current_stock -= 1
        stored_inventory.packs_given += 1
        stored_inventory.updated_at = datetime.now()

        session.commit()

        session.refresh(
            stored_newcomer
        )

        session.refresh(
            stored_inventory
        )

        return (
            "given",
            stored_newcomer,
            stored_inventory,
        )


# =========================================================
# REMOVE / UNDO NEWCOMER
# =========================================================

def remove_newcomer(
    display_name: str,
) -> tuple[
    str,
    str | None,
    bool,
    CareNewcomerInventory | None,
]:
    """Remove mistaken newcomer registration."""

    newcomer = find_newcomer(
        display_name
    )

    if newcomer is None:

        return (
            "not_found",
            None,
            False,
            None,
        )

    newcomer_id = newcomer.id
    newcomer_name = newcomer.display_name
    visit_year = newcomer.first_visit_date.year
    pack_was_given = newcomer.pack_given

    with SessionLocal() as session:

        stored_newcomer = session.get(
            CareNewcomer,
            newcomer_id,
        )

        if stored_newcomer is None:

            return (
                "not_found",
                None,
                False,
                None,
            )

        inventory = session.scalar(
            select(
                CareNewcomerInventory
            ).where(
                CareNewcomerInventory.year
                == visit_year
            )
        )

        pack_restored = False

        if (
            pack_was_given
            and inventory is not None
        ):

            inventory.current_stock += 1

            if inventory.packs_given > 0:
                inventory.packs_given -= 1

            inventory.updated_at = datetime.now()

            pack_restored = True

        session.delete(
            stored_newcomer
        )

        session.commit()

        if inventory is not None:
            session.refresh(
                inventory
            )

        return (
            "removed",
            newcomer_name,
            pack_restored,
            inventory,
        )


# =========================================================
# DISPLAY NEWCOMERS
# =========================================================

def format_newcomer_record(
    newcomer: CareNewcomer,
) -> str:
    """Format one newcomer record."""

    pack_status = (
        "✅ Given"
        if newcomer.pack_given
        else "❌ Not yet given"
    )

    return (
        f"👋 {newcomer.display_name}\n"
        f"📅 First visit: "
        f"{newcomer.first_visit_date.strftime('%d %b %Y')}\n"
        f"🙋 Invited by: {newcomer.invited_by}\n"
        f"🎁 Newcomer pack: {pack_status}"
    )


def format_newcomer_register() -> str:
    """Format recent newcomer register."""

    newcomers = get_recent_newcomers(
        limit=20
    )

    total = get_newcomer_count()

    if not newcomers:

        return (
            "👋 CARE NEWCOMER REGISTER\n\n"
            "No newcomers have been registered yet."
        )

    lines = [
        "👋 CARE NEWCOMER REGISTER",
        "",
        f"Total registered: {total}",
        "",
        "Most recent:",
    ]

    for newcomer in newcomers:

        pack_icon = (
            "🎁"
            if newcomer.pack_given
            else "⚠️"
        )

        lines.append(
            (
                f"{pack_icon} "
                f"{newcomer.display_name} — "
                f"{newcomer.first_visit_date.strftime('%d %b %Y')}"
            )
        )

    if total > len(
        newcomers
    ):

        lines.extend(
            [
                "",
                (
                    f"Showing the latest "
                    f"{len(newcomers)} records."
                ),
            ]
        )

    return "\n".join(
        lines
    )


# =========================================================
# ANNUAL NEWCOMER PACK PREP
# =========================================================

def get_current_newcomer_prep_year() -> int:
    """Return year currently being prepared."""

    return get_singapore_today().year + 1


def get_or_create_newcomer_annual_prep(
    target_year: int,
) -> CareNewcomerAnnualPrep:
    """Get/create annual newcomer pack preparation."""

    if target_year < 2000:
        raise ValueError(
            "Invalid target year."
        )

    with SessionLocal() as session:

        prep = session.scalar(
            select(
                CareNewcomerAnnualPrep
            ).where(
                CareNewcomerAnnualPrep.target_year
                == target_year
            )
        )

        if prep is None:

            prep = CareNewcomerAnnualPrep(
                target_year=target_year,
                target_pack_count=50,
            )

            session.add(
                prep
            )

            session.commit()
            session.refresh(
                prep
            )

        return prep


def toggle_newcomer_annual_prep_item(
    target_year: int,
    item_key: str,
) -> CareNewcomerAnnualPrep:
    """Toggle one annual prep item."""

    checklist_item = (
        NEWCOMER_ANNUAL_PREP_CHECKLIST.get(
            item_key
        )
    )

    if checklist_item is None:

        raise ValueError(
            "Unknown annual prep item."
        )

    field_name = checklist_item[0]

    with SessionLocal() as session:

        prep = session.scalar(
            select(
                CareNewcomerAnnualPrep
            ).where(
                CareNewcomerAnnualPrep.target_year
                == target_year
            )
        )

        if prep is None:

            prep = CareNewcomerAnnualPrep(
                target_year=target_year,
                target_pack_count=50,
            )

            session.add(
                prep
            )

            session.flush()

        current_value = getattr(
            prep,
            field_name,
        )

        setattr(
            prep,
            field_name,
            not current_value,
        )

        prep.updated_at = datetime.now()

        session.commit()
        session.refresh(
            prep
        )

        return prep


def get_incomplete_newcomer_annual_items(
    prep: CareNewcomerAnnualPrep,
) -> list[str]:
    """Return unfinished annual prep items."""

    incomplete = []

    for (
        field_name,
        label,
    ) in NEWCOMER_ANNUAL_PREP_CHECKLIST.values():

        if not getattr(
            prep,
            field_name,
        ):
            incomplete.append(
                label
            )

    return incomplete


def is_newcomer_annual_prep_complete(
    prep: CareNewcomerAnnualPrep,
) -> bool:
    """Check whether annual prep is complete."""

    return not get_incomplete_newcomer_annual_items(
        prep
    )


def format_newcomer_annual_prep(
    target_year: int,
) -> str:
    """Format annual newcomer pack preparation."""

    prep = get_or_create_newcomer_annual_prep(
        target_year
    )

    completed = 0

    lines = [
        f"👋 {target_year} NEWCOMER PACK PREP",
        "",
        f"🎯 Target: {prep.target_pack_count} packs",
        "",
        "📋 PREPARATION",
    ]

    for (
        field_name,
        label,
    ) in NEWCOMER_ANNUAL_PREP_CHECKLIST.values():

        done = getattr(
            prep,
            field_name,
        )

        if done:
            completed += 1

        lines.append(
            f"{'✅' if done else '⬜'} {label}"
        )

    if completed == len(
        NEWCOMER_ANNUAL_PREP_CHECKLIST
    ):
        status = "✅ COMPLETED"

    elif completed == 0:
        status = "⚪ NOT STARTED"

    else:
        status = "🟡 IN PROGRESS"

    lines.extend(
        [
            "",
            status,
            (
                f"Progress: {completed} / "
                f"{len(NEWCOMER_ANNUAL_PREP_CHECKLIST)}"
            ),
            "",
            (
                f"🎯 Goal: packs ready before "
                f"1 January {target_year}."
            ),
        ]
    )

    return "\n".join(
        lines
    )


def build_newcomer_annual_reminder(
    target_year: int,
    heading: str,
    full_checklist: bool = False,
) -> str | None:
    """Build annual newcomer-pack prep reminder."""

    prep = get_or_create_newcomer_annual_prep(
        target_year
    )

    if is_newcomer_annual_prep_complete(
        prep
    ):
        return None

    lines = [
        heading,
        "",
        (
            f"👋 Preparing {prep.target_pack_count} "
            f"newcomer packs for {target_year}"
        ),
        "",
    ]

    if full_checklist:

        for (
            field_name,
            label,
        ) in NEWCOMER_ANNUAL_PREP_CHECKLIST.values():

            done = getattr(
                prep,
                field_name,
            )

            lines.append(
                f"{'✅' if done else '⬜'} {label}"
            )

    else:

        incomplete = (
            get_incomplete_newcomer_annual_items(
                prep
            )
        )

        for item in incomplete:
            lines.append(
                f"⬜ {item}"
            )

    lines.extend(
        [
            "",
            (
                f"🎯 Goal: all {prep.target_pack_count} "
                f"packs ready before "
                f"1 January {target_year}."
            ),
        ]
    )

    return "\n".join(
        lines
    )


def newcomer_annual_reminder_was_sent(
    target_year: int,
    field_name: str,
) -> bool:
    """Check annual reminder flag."""

    allowed_fields = {
        "open_reminder_sent",
        "nov15_reminder_sent",
        "dec1_reminder_sent",
        "dec15_reminder_sent",
        "dec25_reminder_sent",
    }

    if field_name not in allowed_fields:

        raise ValueError(
            "Unknown reminder flag."
        )

    prep = get_or_create_newcomer_annual_prep(
        target_year
    )

    return bool(
        getattr(
            prep,
            field_name,
        )
    )


def mark_newcomer_annual_reminder_sent(
    target_year: int,
    field_name: str,
) -> None:
    """Mark annual reminder as sent."""

    allowed_fields = {
        "open_reminder_sent",
        "nov15_reminder_sent",
        "dec1_reminder_sent",
        "dec15_reminder_sent",
        "dec25_reminder_sent",
    }

    if field_name not in allowed_fields:

        raise ValueError(
            "Unknown reminder flag."
        )

    with SessionLocal() as session:

        prep = session.scalar(
            select(
                CareNewcomerAnnualPrep
            ).where(
                CareNewcomerAnnualPrep.target_year
                == target_year
            )
        )

        if prep is None:

            prep = CareNewcomerAnnualPrep(
                target_year=target_year,
                target_pack_count=50,
            )

            session.add(
                prep
            )

            session.flush()

        setattr(
            prep,
            field_name,
            True,
        )

        prep.updated_at = datetime.now()

        session.commit()


# =========================================================
# MID-YEAR STOCKTAKE
# =========================================================

def build_midyear_stocktake_reminder(
    year: int,
) -> str:
    """Build 1 July stocktake reminder."""

    inventory = get_or_create_newcomer_inventory(
        year
    )

    return (
        f"📦 {year} MID-YEAR NEWCOMER PACK CHECK\n\n"
        f"Dobby currently records:\n"
        f"🎁 Packs remaining: "
        f"{inventory.current_stock}\n\n"
        "Please do a physical stocktake:\n\n"
        "⬜ Count the actual packs on hand\n"
        "⬜ Check whether replenishment is needed\n"
        "⬜ Purchase additional items if required\n"
        "⬜ Pack additional newcomer packs if required\n"
        "⬜ Update Dobby's stock quantity\n\n"
        "If Dobby's number is wrong:\n"
        "/setnewcomerstock QUANTITY\n\n"
        "If you prepared additional packs:\n"
        "/addnewcomerstock QUANTITY"
    )


def midyear_reminder_was_sent(
    year: int,
) -> bool:
    """Check whether mid-year reminder was sent."""

    inventory = get_or_create_newcomer_inventory(
        year
    )

    return bool(
        inventory.midyear_reminder_sent
    )


def mark_midyear_reminder_sent(
    year: int,
) -> None:
    """Mark mid-year reminder as sent."""

    with SessionLocal() as session:

        inventory = session.scalar(
            select(
                CareNewcomerInventory
            ).where(
                CareNewcomerInventory.year
                == year
            )
        )

        if inventory is None:

            inventory = CareNewcomerInventory(
                year=year,
                starting_stock=50,
                current_stock=50,
                packs_given=0,
                replenished_stock=0,
            )

            session.add(
                inventory
            )

            session.flush()

        inventory.midyear_reminder_sent = True
        inventory.updated_at = datetime.now()

        session.commit()