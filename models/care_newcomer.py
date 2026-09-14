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


class CareNewcomer(Base):
    """Permanent CARE newcomer register."""

    __tablename__ = "care_newcomers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    invited_by: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    first_visit_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    pack_given: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )