from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class CareEncouragementRecipient(Base):
    """One youth receiving an encouragement pack."""

    __tablename__ = "care_encouragement_recipients"

    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "person_name",
            name="uq_encouragement_batch_recipient",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    batch_id: Mapped[int] = mapped_column(
        ForeignKey(
            "care_encouragement_batches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    person_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    card_given: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    pack_given: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )