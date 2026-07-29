from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class Member(Base):
    """A member of the life group."""

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True,
    )

    telegram_username: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    birthday_month: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    birthday_day: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    birthday_planner_id: Mapped[int | None] = mapped_column(
        ForeignKey("members.id"),
        nullable=True,
    )

    is_leader: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )