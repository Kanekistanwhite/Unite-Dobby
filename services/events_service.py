from datetime import datetime

from sqlalchemy import select

from database.database import SessionLocal
from models.events_item import EventsItem


def create_events_item(
    item_type: str,
    title: str,
    scheduled_at: datetime,
) -> EventsItem:
    """Create a new Events Team meeting or deadline."""

    cleaned_title = title.strip()
    cleaned_type = item_type.strip().lower()

    if cleaned_type not in {
        "meeting",
        "deadline",
    }:
        raise ValueError(
            "Events item must be either a meeting or deadline."
        )

    if not cleaned_title:
        raise ValueError(
            "The title cannot be empty."
        )

    with SessionLocal() as session:
        item = EventsItem(
            item_type=cleaned_type,
            title=cleaned_title,
            scheduled_at=scheduled_at,
        )

        session.add(item)
        session.commit()
        session.refresh(item)

        return item


def get_upcoming_events_items() -> list[EventsItem]:
    """Return upcoming active Events Team items."""

    now = datetime.now()

    with SessionLocal() as session:
        items = session.scalars(
            select(EventsItem)
            .where(
                EventsItem.is_cancelled.is_(False),
                EventsItem.scheduled_at >= now,
            )
            .order_by(
                EventsItem.scheduled_at,
                EventsItem.id,
            )
        ).all()

        return list(items)


def get_events_item(
    item_id: int,
) -> EventsItem | None:
    """Return one Events Team item by ID."""

    with SessionLocal() as session:
        return session.get(
            EventsItem,
            item_id,
        )


def complete_deadline(
    item_id: int,
) -> EventsItem:
    """Mark a deadline as completed."""

    with SessionLocal() as session:
        item = session.get(
            EventsItem,
            item_id,
        )

        if item is None:
            raise ValueError(
                f"Events item #{item_id} was not found."
            )

        if item.item_type != "deadline":
            raise ValueError(
                f"#{item_id} is not a deadline."
            )

        if item.is_cancelled:
            raise ValueError(
                f"#{item_id} has already been cancelled."
            )

        if item.is_completed:
            raise ValueError(
                f"#{item_id} is already completed."
            )

        item.is_completed = True

        session.commit()
        session.refresh(item)

        return item


def cancel_events_item(
    item_id: int,
) -> EventsItem:
    """Cancel a meeting or deadline."""

    with SessionLocal() as session:
        item = session.get(
            EventsItem,
            item_id,
        )

        if item is None:
            raise ValueError(
                f"Events item #{item_id} was not found."
            )

        if item.is_cancelled:
            raise ValueError(
                f"#{item_id} is already cancelled."
            )

        item.is_cancelled = True

        session.commit()
        session.refresh(item)

        return item