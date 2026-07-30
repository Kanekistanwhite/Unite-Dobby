import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def parse_user_ids(value: str) -> set[int]:
    """Convert comma-separated Telegram IDs into integers."""

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


def read_optional_int(variable_name: str) -> int | None:
    """Read an optional integer from the environment."""

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
    """Read a true-or-false environment setting."""

    default_text = "true" if default else "false"

    value = os.getenv(
        variable_name,
        default_text,
    ).strip().lower()

    if value not in {"true", "false"}:
        raise RuntimeError(
            f"{variable_name} must be either true or false."
        )

    return value == "true"


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Check that the .env file exists "
        "and contains BOT_TOKEN=your_token."
    )


LEADER_USER_IDS = parse_user_ids(
    os.getenv("LEADER_USER_IDS", "")
)


BIRTHDAY_CHAT_ID = read_optional_int(
    "BIRTHDAY_CHAT_ID"
)

BIRTHDAY_SCHEDULER_ENABLED = read_boolean(
    "BIRTHDAY_SCHEDULER_ENABLED"
)


SUNDAY_CHAT_ID = read_optional_int(
    "SUNDAY_CHAT_ID"
)

SUNDAY_SCHEDULER_ENABLED = read_boolean(
    "SUNDAY_SCHEDULER_ENABLED"
)