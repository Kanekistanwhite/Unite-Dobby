from datetime import (
    date,
    datetime,
)

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class CareMilestone(Base):
    """One CARE milestone celebration."""

    __tablename__ = "care_milestones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    person_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    milestone_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    milestone_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    milestone_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Exact date is optional.
    # Useful when CARE only knows the month initially.
    milestone_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # -----------------------------------------------------
    # PREPARATION
    # -----------------------------------------------------

    gift_prepared: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    card_prepared: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # FULFILMENT
    # -----------------------------------------------------

    gift_given: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    card_given: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # REMINDERS
    # -----------------------------------------------------

    planning_reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_cancelled: Mapped[bool] = mapped_column(
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