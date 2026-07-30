from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class BiweeklyEvent(Base):
    """A scheduled bi-weekly life-group meetup."""

    __tablename__ = "biweekly_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    event_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True,
    )

    poll_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    poll_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"BiweeklyEvent("
            f"id={self.id}, "
            f"event_date={self.event_date}, "
            f"poll_date={self.poll_date}"
            f")"
        )