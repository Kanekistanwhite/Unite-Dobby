import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config.settings import (
    BIRTHDAY_CHAT_ID,
    BIRTHDAY_SCHEDULER_ENABLED,
)
from services.birthday_service import (
    get_birthday_member_by_name,
    get_birthdays_for_date,
)
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo("Asia/Singapore")


def build_birthday_message(
    display_name: str,
    telegram_username: str | None,
) -> str:
    """Build a birthday greeting for one member."""

    name_with_username = display_name

    if telegram_username:
        name_with_username += f" (@{telegram_username})"

    return (
        f"🎉 Happy Birthday {name_with_username}!\n\n"
        f"Everyone show {display_name} some birthday love! 🥳🎂"
    )


def leader_is_approved(update: Update) -> bool:
    """Check whether the person using the command is an approved leader."""

    user = update.effective_user
    user_id = user.id if user else None

    return is_approved_leader(user_id)


async def send_daily_birthday_greetings(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Check today's birthdays and send automatic greetings."""

    if BIRTHDAY_CHAT_ID is None:
        logger.warning(
            "Birthday greeting skipped because "
            "BIRTHDAY_CHAT_ID is not configured."
        )
        return

    today = datetime.now(SINGAPORE_TIMEZONE)

    birthdays = get_birthdays_for_date(
        day=today.day,
        month=today.month,
    )

    if not birthdays:
        logger.info(
            "No birthdays today: %02d-%02d",
            today.day,
            today.month,
        )
        return

    for display_name, telegram_username in birthdays:
        message = build_birthday_message(
            display_name=display_name,
            telegram_username=telegram_username,
        )

        await context.bot.send_message(
            chat_id=BIRTHDAY_CHAT_ID,
            text=message,
        )

        logger.info(
            "Birthday greeting sent for %s.",
            display_name,
        )


async def test_birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show a birthday-message preview."""

    if update.message is None:
        return

    if not leader_is_approved(update):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    member_name = " ".join(context.args).strip()

    if not member_name:
        await update.message.reply_text(
            "Usage:\n"
            "/testbirthday Member Name\n\n"
            "Example:\n"
            "/testbirthday Kelly"
        )
        return

    member = get_birthday_member_by_name(member_name)

    if member is None:
        await update.message.reply_text(
            f"❌ Member '{member_name}' was not found."
        )
        return

    display_name, telegram_username = member

    await update.message.reply_text(
        "🧪 Birthday greeting preview\n\n"
        + build_birthday_message(
            display_name=display_name,
            telegram_username=telegram_username,
        )
    )


async def send_birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Send a real birthday greeting into the current chat.

    Use only inside the private test group during development.
    """

    if update.message is None:
        return

    if not leader_is_approved(update):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    chat = update.effective_chat

    if chat is None:
        return

    member_name = " ".join(context.args).strip()

    if not member_name:
        await update.message.reply_text(
            "Usage:\n"
            "/sendbirthday Member Name\n\n"
            "Example:\n"
            "/sendbirthday Kelly"
        )
        return

    member = get_birthday_member_by_name(member_name)

    if member is None:
        await update.message.reply_text(
            f"❌ Member '{member_name}' was not found."
        )
        return

    display_name, telegram_username = member

    message = build_birthday_message(
        display_name=display_name,
        telegram_username=telegram_username,
    )

    await context.bot.send_message(
        chat_id=chat.id,
        text=message,
    )

    logger.info(
        "Manual birthday greeting sent for %s in chat %s.",
        display_name,
        chat.id,
    )


def register_birthday_handlers(
    application: Application,
) -> None:
    """Register birthday commands and the optional scheduler."""

    application.add_handler(
        CommandHandler(
            "testbirthday",
            test_birthday_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "sendbirthday",
            send_birthday_command,
        )
    )

    if not BIRTHDAY_SCHEDULER_ENABLED:
        logger.info(
            "Automatic birthday greetings are disabled."
        )
        return

    if BIRTHDAY_CHAT_ID is None:
        logger.warning(
            "Birthday scheduler was not started because "
            "BIRTHDAY_CHAT_ID is missing."
        )
        return

    if application.job_queue is None:
        raise RuntimeError(
            "Telegram JobQueue is unavailable. "
            'Install "python-telegram-bot[job-queue]".'
        )

    application.job_queue.run_daily(
        callback=send_daily_birthday_greetings,
        time=time(
            hour=0,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        name="daily-birthday-greetings",
    )

    logger.info(
        "Automatic birthday greetings are scheduled for "
        "12:00 AM Singapore time."
    )