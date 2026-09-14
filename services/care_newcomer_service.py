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
from models.care_newcomer_inventory import CareNewcomerInventory


SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


# =========================================================
# TIME
# =========================================================

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
    """
    Set physical newcomer-pack stock.

    Useful when Dobby's starting quantity needs to be
    matched to the team's real physical stock.
    """

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
    """Find a newcomer by case-insensitive exact name."""

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
    """Return total people in the newcomer register."""

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
    """
    Register a newcomer.

    Status values:
    - registered
    - registered_no_pack
    - duplicate
    """

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

        if pack_given:

            status = "registered"

        else:

            status = "registered_no_pack"

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
    """
    Give a pack to a registered newcomer who did not
    receive one previously.

    Status values:
    - given
    - already_given
    - no_stock
    - not_found
    """

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
# DISPLAY
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