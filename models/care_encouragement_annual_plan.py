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


class CareEncouragementAnnualPlan(Base):
    """Annual CARE Encouragement preparation."""

    __tablename__ = "care_encouragement_annual_plans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    target_year: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    # -----------------------------------------------------
    # EDUCATION / EXAM LOOKOUT
    # -----------------------------------------------------

    cell_leaders_contacted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    exam_periods_collected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    crucial_periods_collected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    known_periods_entered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # PACK PREPARATION
    # -----------------------------------------------------

    contents_decided: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    quantity_estimated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

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

    cards_ready: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    initial_stock_prepared: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # REMINDER FLAGS
    # -----------------------------------------------------

    lookout_open_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    lookout_followup_sent: Mapped[bool] = mapped_column(
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