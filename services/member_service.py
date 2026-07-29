from sqlalchemy import func, select

from database.database import SessionLocal
from models.member import Member


def add_member(
    display_name: str,
    birthday_day: int,
    birthday_month: int,
    is_leader: bool = False,
) -> Member:
    """Create and save a new life-group member."""

    cleaned_name = display_name.strip()

    if not cleaned_name:
        raise ValueError("The member name cannot be empty.")

    if birthday_month < 1 or birthday_month > 12:
        raise ValueError("Birthday month must be between 1 and 12.")

    if birthday_day < 1 or birthday_day > 31:
        raise ValueError("Birthday day must be between 1 and 31.")

    with SessionLocal() as session:
        existing_member = session.scalar(
            select(Member).where(
                func.lower(Member.display_name)
                == cleaned_name.lower()
            )
        )

        if existing_member:
            raise ValueError(
                f"{cleaned_name} already exists in the database."
            )

        member = Member(
            display_name=cleaned_name,
            birthday_day=birthday_day,
            birthday_month=birthday_month,
            is_leader=is_leader,
            is_active=True,
        )

        session.add(member)
        session.commit()
        session.refresh(member)

        return member


def get_active_members() -> list[Member]:
    """Return all active members in alphabetical order."""

    with SessionLocal() as session:
        members = session.scalars(
            select(Member)
            .where(Member.is_active.is_(True))
            .order_by(Member.display_name)
        ).all()

        return list(members)
    