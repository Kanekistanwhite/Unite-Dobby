import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
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


LEADER_USER_IDS = parse_user_ids(
    os.getenv("LEADER_USER_IDS", "")
)
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Check that the .env file exists "
        "and contains BOT_TOKEN=your_token."
    )