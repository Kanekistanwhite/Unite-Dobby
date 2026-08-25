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
    SUNDAY_TOPIC_ID,
)
from services.date_service import (
    format_full_date,
    format_short_date,
    get_upcoming_sunday,
)
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo("Asia/Singapore")


# ---------------------------------------------------------
# SUNDAY POLL SETTINGS
# ---------------------------------------------------------

SUNDAY_POLL_OPTIONS = [
    "⛪ Morning Service",
    "🍽 Lunch",
    "🔥 Youth Service",
    "🤝 Hangout Afterwards",
    "🙌 Serving",
    "❌ CMI All",
]


# ---------------------------------------------------------
# PERMISSION CHECK
# ---------------------------------------------------------

async def check_leader_permission(
    update: Update,
) -> bool:
    """Allow only approved leaders to use Sunday commands."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return False

    user_id = user.id if user else None

    if not is_approved_leader(user_id):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return False

    return True


# ---------------------------------------------------------
# SEND SUNDAY POLL
# ---------------------------------------------------------

async def send_sunday_poll(
    bot: Bot,
    chat_id: int,
    topic_id: int | None = None,
) -> None:
    """Send the Sunday attendance message and poll."""

    sunday_date = get_upcoming_sunday()

    full_date = format_full_date(
        sunday_date
    )

    short_date = format_short_date(
        sunday_date
    )

    thread_kwargs = {}

    if topic_id is not None:
        thread_kwargs["message_thread_id"] = topic_id

    await bot.send_message(
        chat_id=chat_id,
        text=(
            "⛪ SUNDAY ATTENDANCE\n\n"
            f"📅 {full_date}\n\n"
            "Another Sunday, another Poll\n"
            "Please select everything that you will be "
            "joining this Sunday."
        ),
        **thread_kwargs,
    )

    await bot.send_poll(
        chat_id=chat_id,
        question=(
            "What will you be joining this Sunday?\n"
            f"📅 {short_date}"
        ),
        options=SUNDAY_POLL_OPTIONS,
        is_anonymous=False,
        allows_multiple_answers=True,
        **thread_kwargs,
    )


# ---------------------------------------------------------
# CONFIGURED SUNDAY POLL
# ---------------------------------------------------------

async def send_scheduled_sunday_poll(
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """
    Send the Sunday poll to the configured UNITE destination.

    Returns True when successfully sent.
    """

    if SUNDAY_CHAT_ID is None:
        logger.error(
            "SUNDAY_CHAT_ID is not configured."
        )
        return False

    try:
        await send_sunday_poll(
            bot=context.bot,
            chat_id=SUNDAY_CHAT_ID,
            topic_id=SUNDAY_TOPIC_ID,
        )

        logger.info(
            "Sunday attendance poll sent successfully."
        )

        return True

    except Exception:
        logger.exception(
            "Failed to send Sunday attendance poll."
        )

        return False


# ---------------------------------------------------------
# AUTOMATIC TUESDAY JOB
# ---------------------------------------------------------

async def scheduled_sunday_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Automatically send the Sunday poll."""

    logger.info(
        "Running scheduled Sunday attendance poll."
    )

    sent = await send_scheduled_sunday_poll(
        context
    )

    if not sent:
        logger.error(
            "Scheduled Sunday poll was not sent."
        )


# ---------------------------------------------------------
# /testsunday
# ---------------------------------------------------------

async def test_sunday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Send a test Sunday poll into the current chat.

    This does NOT send to the configured UNITE topic.
    """

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    chat = update.effective_chat

    if chat is None:
        return

    topic_id = getattr(
        message,
        "message_thread_id",
        None,
    )

    await message.reply_text(
        "🧪 Sending a test Sunday poll here..."
    )

    try:
        await send_sunday_poll(
            bot=context.bot,
            chat_id=chat.id,
            topic_id=topic_id,
        )

    except Exception:
        logger.exception(
            "Test Sunday poll failed."
        )

        await message.reply_text(
            "❌ The test Sunday poll could not be sent."
        )
        return

    await message.reply_text(
        "✅ Test Sunday poll sent."
    )


# ---------------------------------------------------------
# /sendsunday
# ---------------------------------------------------------

async def send_sunday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Manually send the Sunday poll to the configured destination."""

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "⏳ Sending the Sunday poll..."
    )

    sent = await send_scheduled_sunday_poll(
        context
    )

    if sent:
        await message.reply_text(
            "✅ Sunday poll sent to the configured group topic."
        )
    else:
        await message.reply_text(
            "❌ The Sunday poll could not be sent.\n\n"
            "Check the Railway logs and Sunday configuration."
        )


# ---------------------------------------------------------
# /runsundaycheck
# ---------------------------------------------------------

async def run_sunday_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Run the Sunday poll manually.

    This function is also used by the leader control panel.
    """

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    sent = await send_scheduled_sunday_poll(
        context
    )

    if sent:
        await message.reply_text(
            "✅ Sunday poll sent successfully."
        )
    else:
        await message.reply_text(
            "❌ The Sunday poll could not be sent.\n\n"
            "Check the Railway logs for details."
        )


# ---------------------------------------------------------
# REGISTER HANDLERS + AUTOMATION
# ---------------------------------------------------------

def register_sunday_handlers(
    application: Application,
) -> None:
    """Register Sunday commands and the Tuesday scheduler."""

    application.add_handler(
        CommandHandler(
            "testsunday",
            test_sunday_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "sendsunday",
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
            "Sunday scheduler is disabled."
        )
        return

    if application.job_queue is None:
        logger.error(
            "JobQueue is unavailable. "
            "Sunday scheduler was not started."
        )
        return

    application.job_queue.run_daily(
        scheduled_sunday_job,
        time=time(
            hour=20,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        days=(2,),
        name="sunday_attendance_poll",
    )

    logger.info(
        "Sunday scheduler enabled: "
        "Tuesday at 8:00 PM Singapore time."
    )