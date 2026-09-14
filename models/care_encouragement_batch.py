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


class CareEncouragementBatch(Base):
    """One CARE Encouragement period / batch."""

    __tablename__ = "care_encouragement_batches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    encouragement_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    encouragement_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Exact dates are optional.
    # We may initially only know the month.
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Team packing session.
    packing_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # -----------------------------------------------------
    # PREPARATION CHECKLIST
    # -----------------------------------------------------

    recipient_list_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    cards_ready: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    packs_ready: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    packing_date_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # PACKING / FULFILMENT
    # -----------------------------------------------------

    packs_packed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    cards_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    distribution_completed: Mapped[bool] = mapped_column(
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