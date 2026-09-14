from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class CareNewcomerInventory(Base):
    """Yearly CARE newcomer-pack inventory."""

    __tablename__ = "care_newcomer_inventory"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    starting_stock: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )

    current_stock: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )

    packs_given: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    replenished_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    low_stock_threshold: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # -----------------------------------------------------
    # MID-YEAR STOCKTAKE
    # -----------------------------------------------------

    physical_stock_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # None = decision not made yet
    # True = replenishment required
    # False = replenishment not required
    replenishment_needed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    replenishment_purchased: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    replenishment_packed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    stock_quantity_updated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    midyear_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )