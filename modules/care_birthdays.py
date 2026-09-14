from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config.settings import CARE_LEADER_USER_IDS
from services.care_birthday_service import (
    format_care_birthday_month,
    seed_care_birthday_roster,
)


def is_care_leader(
    user_id: int | None,
) -> bool:
    """Check whether a user may manage CARE Team."""

    if user_id is None:
        return False

    return user_id in CARE_LEADER_USER_IDS


async def check_care_permission(
    update: Update,
) -> bool:
    """Allow only approved CARE Team leaders."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return False

    user_id = (
        user.id
        if user
        else None
    )

    if not is_care_leader(
        user_id
    ):
        await message.reply_text(
            "⛔ This command is only available "
            "to approved CARE Team leaders."
        )
        return False

    return True


async def setup_care_birthdays_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Load the CARE Birthday roster."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "⏳ Updating CARE Birthday roster..."
    )

    created, updated = (
        seed_care_birthday_roster()
    )

    await message.reply_text(
        "✅ CARE BIRTHDAY ROSTER UPDATED\n\n"
        f"New members: {created}\n"
        f"Existing members updated: {updated}"
    )


async def care_birthday_month_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show birthdays and celebration date for a month."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:
        await message.reply_text(
            "Usage:\n"
            "/carebirthdaymonth MM-YYYY\n\n"
            "Example:\n"
            "/carebirthdaymonth 10-2026"
        )
        return

    try:
        month_text, year_text = (
            context.args[0].split(
                "-",
                maxsplit=1,
            )
        )

        month = int(
            month_text
        )

        year = int(
            year_text
        )

        datetime(
            year,
            month,
            1,
        )

    except (
        ValueError,
        TypeError,
    ):
        await message.reply_text(
            "❌ Invalid month.\n\n"
            "Please use MM-YYYY.\n\n"
            "Example:\n"
            "/carebirthdaymonth 10-2026"
        )
        return

    summary = format_care_birthday_month(
        year,
        month,
    )

    await message.reply_text(
        summary
    )


def register_care_birthday_handlers(
    application: Application,
) -> None:
    """Register CARE Birthday commands."""

    application.add_handler(
        CommandHandler(
            "setupcarebirthdays",
            setup_care_birthdays_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "carebirthdaymonth",
            care_birthday_month_command,
        )
    )