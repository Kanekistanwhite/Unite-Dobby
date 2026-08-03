import os
from pathlib import Path

from dotenv import load_dotenv


# Locate the main Unite Dobby project folder.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load private settings from .env during local development.
# Railway provides the same values as environment variables.
load_dotenv(ENV_FILE)


def require_environment_variable(
    variable_name: str,
) -> str:
    """Read a required environment variable."""

    value = os.getenv(variable_name, "").strip()

    if not value:
        raise RuntimeError(
            f"{variable_name} is missing from the environment."
        )

    return value


def parse_user_ids(
    value: str,
) -> set[int]:
    """Convert comma-separated Telegram user IDs into integers."""

    user_ids: set[int] = set()

    for item in value.split(","):
        cleaned_item = item.strip()

        if not cleaned_item:
            continue

        try:
            user_ids.add(int(cleaned_item))
        except ValueError as error:
            raise RuntimeError(
                "LEADER_USER_IDS must contain only Telegram user IDs "
                "separated by commas."
            ) from error

    return user_ids


def read_optional_int(
    variable_name: str,
) -> int | None:
    """Read an optional integer environment variable."""

    value = os.getenv(variable_name, "").strip()

    if not value:
        return None

    try:
        return int(value)
    except ValueError as error:
        raise RuntimeError(
            f"{variable_name} must be a valid Telegram chat ID."
        ) from error


def read_boolean(
    variable_name: str,
    default: bool = False,
) -> bool:
    """Read a true-or-false environment variable."""

    raw_value = os.getenv(variable_name)

    if raw_value is None or not raw_value.strip():
        return default

    value = raw_value.strip().lower()

    if value not in {"true", "false"}:
        raise RuntimeError(
            f"{variable_name} must be either true or false."
        )

    return value == "true"


# Telegram bot configuration.
BOT_TOKEN = require_environment_variable(
    "BOT_TOKEN"
)

LEADER_USER_IDS = parse_user_ids(
    os.getenv("LEADER_USER_IDS", "")
)


# Public birthday greeting configuration.
BIRTHDAY_CHAT_ID = read_optional_int(
    "BIRTHDAY_CHAT_ID"
)

BIRTHDAY_SCHEDULER_ENABLED = read_boolean(
    "BIRTHDAY_SCHEDULER_ENABLED",
    default=False,
)


# Private birthday-planning reminder configuration.
BIRTHDAY_PLANNING_CHAT_ID = read_optional_int(
    "BIRTHDAY_PLANNING_CHAT_ID"
)

BIRTHDAY_PLANNING_SCHEDULER_ENABLED = read_boolean(
    "BIRTHDAY_PLANNING_SCHEDULER_ENABLED",
    default=False,
)


# Sunday attendance configuration.
SUNDAY_CHAT_ID = read_optional_int(
    "SUNDAY_CHAT_ID"
)

SUNDAY_SCHEDULER_ENABLED = read_boolean(
    "SUNDAY_SCHEDULER_ENABLED",
    default=False,
)


# Bi-weekly attendance configuration.
BIWEEKLY_CHAT_ID = read_optional_int(
    "BIWEEKLY_CHAT_ID"
)

BIWEEKLY_SCHEDULER_ENABLED = read_boolean(
    "BIWEEKLY_SCHEDULER_ENABLED",
    default=False,
)