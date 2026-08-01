import logging
from datetime import time
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
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo("Asia/Singapore")

SUNDAY_POLL_OPTIONS = [
    "Morning Service",
    "Lunch",
    "Youth Service",
    "Hangout Afterwards",
    "CMI All",
]


def leader_is_approved(update: Update) -> bool:
    """Check whether the user is an approved leader."""

    user = update.effective_user
    user_id = user.id if user else None

    return is_approved_leader(user_id)


async def post_sunday_poll(
    bot: Bot,
    chat_id: int,
) -> None:
    """Post the Sunday attendance message and native poll."""

    await bot.send_message(
        chat_id=chat_id,
        text=(
            "⛪ Sunday Attendance\n\n"
            "Select everything you can attend.\n"
            "Choose CMI All only if you cannot make it "
            "for anything."
        ),
    )

    await bot.send_poll(
        chat_id=chat_id,
        question="Attendance for this Sunday",
        options=SUNDAY_POLL_OPTIONS,
        is_anonymous=False,
        allows_multiple_answers=True,
        allows_revoting=True,
    )

    logger.info(
        "Sunday attendance poll sent to chat %s.",
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
    """Test the configured Sunday poll destination immediately."""

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
    """Register Sunday commands and the optional schedule."""

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