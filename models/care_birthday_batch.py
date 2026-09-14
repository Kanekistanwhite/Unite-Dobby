from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class CareBirthdayBatch(Base):
    """One monthly CARE Birthday preparation batch."""

    __tablename__ = "care_birthday_batches"

    __table_args__ = (
        UniqueConstraint(
            "year",
            "month",
            name="uq_care_birthday_batch_year_month",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Preparation checklist
    celebrant_list_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    celebration_idea_ready: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    cake_arranged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    gift_packs_ready: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    birthday_cards_ready: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Future workflow stages
    monthly_announcement_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    celebration_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    distribution_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Reminder tracking
    open_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    midmonth_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    final_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    post_celebration_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    last_distribution_reminder_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )