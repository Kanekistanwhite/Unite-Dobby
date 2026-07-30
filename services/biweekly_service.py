from datetime import date, datetime, timedelta

from sqlalchemy import select

from database.database import SessionLocal
from models.biweekly_event import BiweeklyEvent


def parse_event_date(
    event_date_text: str,
) -> date:
    """Convert DD-MM-YYYY text into a Python date."""

    cleaned_date = event_date_text.strip()

    try:
        return datetime.strptime(
            cleaned_date,
            "%d-%m-%Y",
        ).date()

    except ValueError as error:
        raise ValueError(
            "Please enter the date in DD-MM-YYYY format."
        ) from error


def create_biweekly_event(
    event_date_text: str,
) -> BiweeklyEvent:
    """Create a bi-weekly event and calculate its poll date."""

    event_date = parse_event_date(
        event_date_text
    )

    poll_date = event_date - timedelta(
        days=10
    )

    with SessionLocal() as session:
        existing_event = session.scalar(
            select(BiweeklyEvent).where(
                BiweeklyEvent.event_date == event_date
            )
        )

        if existing_event is not None:
            raise ValueError(
                "A bi-weekly event already exists on "
                f"{event_date.strftime('%d-%m-%Y')}."
            )

        event = BiweeklyEvent(
            event_date=event_date,
            poll_date=poll_date,
            poll_sent=False,
            is_active=True,
        )

        session.add(event)
        session.commit()
        session.refresh(event)

        return event


def get_upcoming_biweekly_events() -> list[BiweeklyEvent]:
    """Return active bi-weekly events from today onwards."""

    current_date = date.today()

    with SessionLocal() as session:
        events = session.scalars(
            select(BiweeklyEvent)
            .where(
                BiweeklyEvent.is_active.is_(True),
                BiweeklyEvent.event_date >= current_date,
            )
            .order_by(
                BiweeklyEvent.event_date
            )
        ).all()

        return list(events)


def get_biweekly_event_by_date(
    event_date_text: str,
) -> BiweeklyEvent | None:
    """Find a bi-weekly event using DD-MM-YYYY."""

    event_date = parse_event_date(
        event_date_text
    )

    with SessionLocal() as session:
        event = session.scalar(
            select(BiweeklyEvent).where(
                BiweeklyEvent.event_date == event_date
            )
        )

        return event


def get_pending_biweekly_events(
    current_date: date,
) -> list[BiweeklyEvent]:
    """
    Return events whose automatic poll should be sent.

    An event is pending when:
    - it is active
    - its poll has not already been sent
    - its poll date has arrived
    - its meetup date has not passed
    """

    with SessionLocal() as session:
        events = session.scalars(
            select(BiweeklyEvent)
            .where(
                BiweeklyEvent.is_active.is_(True),
                BiweeklyEvent.poll_sent.is_(False),
                BiweeklyEvent.poll_date <= current_date,
                BiweeklyEvent.event_date >= current_date,
            )
            .order_by(
                BiweeklyEvent.event_date
            )
        ).all()

        return list(events)


def mark_biweekly_poll_sent(
    event_id: int,
) -> None:
    """Mark an event's automatic poll as sent."""

    with SessionLocal() as session:
        event = session.get(
            BiweeklyEvent,
            event_id,
        )

        if event is None:
            raise ValueError(
                f"Bi-weekly event ID {event_id} was not found."
            )

        event.poll_sent = True
        session.commit()