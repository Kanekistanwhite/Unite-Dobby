import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config.settings import (
    SUNDAY_CHAT_ID,
    SUNDAY_SCHEDULER_ENABLED,
)
from services.date_service import (
    format_full_date,
    format_short_date,
    get_upcoming_sunday,
)
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo("Asia/Singapore")

SUNDAY_POLL_OPTIONS = [
    "⛪ Morning Service",
    "🍽 Lunch",
    "🔥 Youth Service",
    "🤝 Hangout Afterwards",
    "❌ CMI All",
]


def leader_is_approved(
    update: Update,
) -> bool:
    """Check whether the user is an approved leader."""

    user = update.effective_user
    user_id = user.id if user else None

    return is_approved_leader(user_id)


def get_next_sunday():
    """Return the upcoming Sunday using Singapore's current date."""

    today = datetime.now(
        SINGAPORE_TIMEZONE
    ).date()

    return get_upcoming_sunday(
        reference_date=today
    )


async def post_sunday_poll(
    bot: Bot,
    chat_id: int,
) -> None:
    """Post the customised Sunday attendance poll."""

    sunday_date = get_next_sunday()

    full_date = format_full_date(
        sunday_date
    )

    short_date = format_short_date(
        sunday_date
    )

    await bot.send_message(
        chat_id=chat_id,
        text=(
            "⛪ SUNDAY ATTENDANCE\n\n"
            f"📅 {full_date}\n\n"
            "Another Sunday, another Poll\n"
            "Please select everything that you will be "
            "joining this Sunday."
        ),
    )

    await bot.send_poll(
        chat_id=chat_id,
        question=(
            "What will you be joining this Sunday?\n"
            f"{short_date}"
        ),
        options=SUNDAY_POLL_OPTIONS,
        is_anonymous=False,
        allows_multiple_answers=True,
        allows_revoting=True,
    )

    logger.info(
        "Sunday attendance poll for %s sent to chat %s.",
        sunday_date,
        chat_id,
    )


async def send_sunday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Post a Sunday poll into the same chat as the command."""

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

    await post_sunday_poll(
        bot=context.bot,
        chat_id=chat.id,
    )


async def send_scheduled_sunday_poll(
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Send the Sunday poll to the configured Sunday chat."""

    if SUNDAY_CHAT_ID is None:
        logger.warning(
            "Sunday poll skipped because "
            "SUNDAY_CHAT_ID is not configured."
        )
        return False

    await post_sunday_poll(
        bot=context.bot,
        chat_id=SUNDAY_CHAT_ID,
    )

    return True


async def run_sunday_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Test the configured Sunday poll destination."""

    if update.message is None:
        return

    if not leader_is_approved(update):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    if SUNDAY_CHAT_ID is None:
        await update.message.reply_text(
            "❌ SUNDAY_CHAT_ID is not configured.\n\n"
            "Add the private test-group chat ID "
            "to Railway Variables."
        )
        return

    await update.message.reply_text(
        "🔍 Testing the configured Sunday poll destination..."
    )

    sent = await send_scheduled_sunday_poll(
        context
    )

    if sent:
        await update.message.reply_text(
            "✅ Sunday poll sent to the configured test chat."
        )
    else:
        await update.message.reply_text(
            "❌ The Sunday poll could not be sent."
        )


def register_sunday_handlers(
    application: Application,
) -> None:
    """Register Sunday commands and the optional scheduler."""

    application.add_handler(
        CommandHandler(
            "sendsunday",
            send_sunday_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "testsunday",
            send_sunday_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runsundaycheck",
            run_sunday_check_command,
        )
    )

    if not SUNDAY_SCHEDULER_ENABLED:
        logger.info(
            "Automatic Sunday attendance polls are disabled."
        )
        return

    if SUNDAY_CHAT_ID is None:
        logger.warning(
            "Sunday scheduler was not started because "
            "SUNDAY_CHAT_ID is missing."
        )
        return

    if application.job_queue is None:
        raise RuntimeError(
            "Telegram JobQueue is unavailable. "
            'Install "python-telegram-bot[job-queue]".'
        )

    application.job_queue.run_daily(
        callback=send_scheduled_sunday_poll,
        time=time(
            hour=20,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        days=(4,),
        name="weekly-sunday-attendance-poll",
    )

    logger.info(
        "Sunday attendance poll scheduled for "
        "Thursday at 8:00 PM Singapore time."
    )