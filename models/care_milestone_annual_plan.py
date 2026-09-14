from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class CareMilestoneAnnualPlan(Base):
    """Annual CARE Milestone planning for one year."""

    __tablename__ = "care_milestone_annual_plans"

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
    # GIFT TYPES
    # -----------------------------------------------------

    secondary_gift: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    polytechnic_gift: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    jc_gift: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    university_gift: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    baptism_gift: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    ord_gift: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    # -----------------------------------------------------
    # MILESTONE LOOKOUT
    # -----------------------------------------------------

    cell_leaders_contacted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    responses_collected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    known_milestones_entered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # -----------------------------------------------------
    # AUTOMATIC REMINDER FLAGS
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

    year_start_tracker_sent: Mapped[bool] = mapped_column(
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