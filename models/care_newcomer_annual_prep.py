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


class CareNewcomerAnnualPrep(Base):
    """Annual newcomer-pack preparation for the next year."""

    __tablename__ = "care_newcomer_annual_prep"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    target_year: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    target_pack_count: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )

    # -----------------------------------------------------
    # PLANNING
    # -----------------------------------------------------

    contents_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    quantity_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # PURCHASING
    # -----------------------------------------------------

    items_purchased: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    packaging_purchased: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    all_items_arrived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # PACKING
    # -----------------------------------------------------

    packs_packed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    final_stock_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # AUTOMATIC REMINDER FLAGS
    # -----------------------------------------------------

    open_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    nov15_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    dec1_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    dec15_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    dec25_reminder_sent: Mapped[bool] = mapped_column(
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