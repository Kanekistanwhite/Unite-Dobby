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


class CareBirthdayAnnualPrep(Base):
    """Annual birthday gift preparation for one target year."""

    __tablename__ = "care_birthday_annual_prep"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    target_year: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    # Planning
    gift_finalised: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    quantity_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Purchasing
    gifts_purchased: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    packing_materials_purchased: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    all_items_arrived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Packing
    gifts_packed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    packs_counted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    sufficient_stock_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Reminder flags
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