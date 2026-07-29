from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

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

    try:
        # Year 2000 allows valid leap-day birthdays.
        date(2000, birthday_month, birthday_day)
    except ValueError as error:
        raise ValueError(
            "Please enter a valid birthday in DD-MM format."
        ) from error

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
    """Return active members in alphabetical order."""

    with SessionLocal() as session:
        members = session.scalars(
            select(Member)
            .where(Member.is_active.is_(True))
            .order_by(Member.display_name)
        ).all()

        return list(members)


def get_active_members_with_planners(
) -> list[tuple[Member, str | None]]:
    """Return active members together with their planner names."""

    Planner = aliased(Member)

    with SessionLocal() as session:
        rows = session.execute(
            select(
                Member,
                Planner.display_name,
            )
            .outerjoin(
                Planner,
                Member.birthday_planner_id == Planner.id,
            )
            .where(Member.is_active.is_(True))
            .order_by(Member.display_name)
        ).all()

        return [
            (member, planner_name)
            for member, planner_name in rows
        ]


def set_birthday_planner(
    member_name: str,
    planner_name: str,
) -> tuple[Member, Member]:
    """Assign an existing member as another member's planner."""

    cleaned_member_name = member_name.strip()
    cleaned_planner_name = planner_name.strip()

    if not cleaned_member_name or not cleaned_planner_name:
        raise ValueError(
            "Both the member and planner names are required."
        )

    with SessionLocal() as session:
        member = session.scalar(
            select(Member).where(
                func.lower(Member.display_name)
                == cleaned_member_name.lower()
            )
        )

        if member is None:
            raise ValueError(
                f"Member '{cleaned_member_name}' was not found."
            )

        planner = session.scalar(
            select(Member).where(
                func.lower(Member.display_name)
                == cleaned_planner_name.lower()
            )
        )

        if planner is None:
            raise ValueError(
                f"Planner '{cleaned_planner_name}' was not found."
            )

        if not member.is_active:
            raise ValueError(
                f"{member.display_name} is not an active member."
            )

        if not planner.is_active:
            raise ValueError(
                f"{planner.display_name} is not an active member."
            )

        member.birthday_planner_id = planner.id

        session.commit()
        session.refresh(member)
        session.refresh(planner)

        return member, planner