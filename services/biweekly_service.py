from datetime import date, datetime, timedelta

from sqlalchemy import select

from database.database import SessionLocal
from models.biweekly_event import BiweeklyEvent


def parse_event_date(event_date_text: str) -> date:
    """Convert DD-MM-YYYY text into a date."""

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

    event_date = parse_event_date(event_date_text)
    poll_date = event_date - timedelta(days=10)

    with SessionLocal() as session:
        existing_event = session.scalar(
            select(BiweeklyEvent).where(
                BiweeklyEvent.event_date == event_date
            )
        )

        if existing_event:
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

    today = date.today()

    with SessionLocal() as session:
        events = session.scalars(
            select(BiweeklyEvent)
            .where(
                BiweeklyEvent.is_active.is_(True),
                BiweeklyEvent.event_date >= today,
            )
            .order_by(BiweeklyEvent.event_date)
        ).all()

        return list(events)


def get_biweekly_event_by_date(
    event_date_text: str,
) -> BiweeklyEvent | None:
    """Find a bi-weekly event using its event date."""

    event_date = parse_event_date(event_date_text)

    with SessionLocal() as session:
        return session.scalar(
            select(BiweeklyEvent).where(
                BiweeklyEvent.event_date == event_date
            )
        )