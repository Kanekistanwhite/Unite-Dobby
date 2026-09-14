from sqlalchemy import (
    Boolean,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class CareBirthdayMember(Base):
    """A member included in the CARE Birthday roster."""

    __tablename__ = "care_birthday_members"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    birthday_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    birthday_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )