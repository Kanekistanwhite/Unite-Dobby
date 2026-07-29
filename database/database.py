from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_DIRECTORY = Path(__file__).resolve().parent
DATABASE_DIRECTORY.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIRECTORY / "unite_dobby.db"

DATABASE_URL = URL.create(
    drivername="sqlite",
    database=str(DATABASE_PATH),
)


class Base(DeclarativeBase):
    """Base class inherited by all database models."""

    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def init_database() -> None:
    """Create all database tables that do not already exist."""

    # Importing the model registers it with Base before tables are created.
    import models.member  # noqa: F401

    Base.metadata.create_all(bind=engine)