import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)


DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parent
    / "unite_dobby.db"
)

DATABASE_PATH = Path(
    os.getenv(
        "DATABASE_PATH",
        str(DEFAULT_DATABASE_PATH),
    )
).expanduser()

DATABASE_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_URL = URL.create(
    drivername="sqlite",
    database=str(DATABASE_PATH),
)


class Base(DeclarativeBase):
    """Base class inherited by all database models."""

    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def init_database() -> None:
    """Create all database tables that do not already exist."""

    import models.biweekly_event  # noqa: F401

    # CARE Birthdays
    import models.care_birthday_annual_prep  # noqa: F401
    import models.care_birthday_batch  # noqa: F401
    import models.care_birthday_member  # noqa: F401
    import models.care_birthday_reminder  # noqa: F401

    # CARE Newcomers
    import models.care_newcomer  # noqa: F401
    import models.care_newcomer_annual_prep  # noqa: F401
    import models.care_newcomer_inventory  # noqa: F401

    import models.events_item  # noqa: F401
    import models.member  # noqa: F401

    Base.metadata.create_all(
        bind=engine,
    )