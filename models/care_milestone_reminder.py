from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class CareMilestoneReminder(Base):
    """Record CARE Milestone reminders that were sent."""

    __tablename__ = "care_milestone_reminders"

    __table_args__ = (
        UniqueConstraint(
            "year",
            "month",
            "reminder_type",
            name="uq_care_milestone_reminder",
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

    reminder_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )