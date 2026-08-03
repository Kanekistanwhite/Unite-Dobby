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
    BIWEEKLY_CHAT_ID,
    BIWEEKLY_SCHEDULER_ENABLED,
    BIWEEKLY_TOPIC_ID,
)
from services.biweekly_service import (
    create_biweekly_event,
    get_biweekly_event_by_date,
    get_pending_biweekly_events,
    get_upcoming_biweekly_events,
    mark_biweekly_poll_sent,
)
from services.date_service import (
    format_full_date,
    format_short_date,
)
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo("Asia/Singapore")

BIWEEKLY_POLL_OPTIONS = [
    "🍽 Lunch",
    "🌙 Dinner",
    "❌ Cannot Make Both",
]


def leader_is_approved(
    update: Update,
) -> bool:
    """Check whether the command user is an approved leader."""

    user = update.effective_user
    user_id = user.id if user else None

    return is_approved_leader(user_id)


async def post_biweekly_poll(
    bot: Bot,
    chat_id: int,
    event_date_text: str,
    message_thread_id: int | None = None,
) -> None:
    """Post the customised bi-weekly attendance poll."""

    event = get_biweekly_event_by_date(
        event_date_text
    )

    if event is None:
        raise ValueError(
            f"No bi-weekly event exists on {event_date_text}."
        )

    full_date = format_full_date(
        event.event_date
    )

    short_date = format_short_date(
        event.event_date
    )

    await bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=(
            "🏠 UNITE BI-WEEKLY ATTENDANCE\n\n"
            f"📅 {full_date}\n\n"
            "Please indicate which part of the gathering "
            "you can attend.\n\n"
            "You may select both Lunch and Dinner "
            "if you are attending both."
        ),
    )

    await bot.send_poll(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        question=(
            "Which part of the gathering can you attend?\n"
            f"{short_date}"
        ),
        options=BIWEEKLY_POLL_OPTIONS,
        is_anonymous=False,
        allows_multiple_answers=True,
        allows_revoting=True,
    )

    logger.info(
        "Bi-weekly poll for %s sent to chat %s, topic %s.",
        event_date_text,
        chat_id,
        message_thread_id,
    )


async def create_biweekly_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Create an event using /createbiweekly DD-MM-YYYY."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    event_date_text = " ".join(
        context.args
    ).strip()

    if not event_date_text:
        await message.reply_text(
            "Usage:\n"
            "/createbiweekly DD-MM-YYYY\n\n"
            "Example:\n"
            "/createbiweekly 09-08-2026"
        )
        return

    try:
        event = create_biweekly_event(
            event_date_text
        )

    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    await message.reply_text(
        "✅ Bi-weekly event created\n\n"
        f"Meetup date: {format_full_date(event.event_date)}\n"
        f"Poll date: {format_full_date(event.poll_date)}\n\n"
        "The poll is scheduled 10 days before the meetup."
    )


async def list_biweekly_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """List all upcoming active bi-weekly events."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    events = get_upcoming_biweekly_events()

    if not events:
        await message.reply_text(
            "There are no upcoming bi-weekly events."
        )
        return

    event_sections: list[str] = []

    for index, event in enumerate(
        events,
        start=1,
    ):
        poll_status = (
            "✅ Sent"
            if event.poll_sent
            else "⏳ Pending"
        )

        event_sections.append(
            f"{index}. {format_full_date(event.event_date)}\n"
            f"   Poll date: {format_full_date(event.poll_date)}\n"
            f"   Poll status: {poll_status}"
        )

    await message.reply_text(
        "🏠 Upcoming UNITE Bi-weekly Events\n\n"
        + "\n\n".join(event_sections)
    )


async def send_biweekly_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send a bi-weekly poll into the current chat or topic."""

    message = update.effective_message
    chat = update.effective_chat

    if message is None or chat is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    event_date_text = " ".join(
        context.args
    ).strip()

    if not event_date_text:
        await message.reply_text(
            "Usage:\n"
            "/sendbiweekly DD-MM-YYYY\n\n"
            "Example:\n"
            "/sendbiweekly 09-08-2026"
        )
        return

    try:
        await post_biweekly_poll(
            bot=context.bot,
            chat_id=chat.id,
            event_date_text=event_date_text,
            message_thread_id=message.message_thread_id,
        )

    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )


async def send_scheduled_biweekly_polls(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Send pending polls to the configured group topic."""

    if BIWEEKLY_CHAT_ID is None:
        logger.warning(
            "Bi-weekly poll check skipped because "
            "BIWEEKLY_CHAT_ID is not configured."
        )
        return 0

    if BIWEEKLY_TOPIC_ID is None:
        logger.warning(
            "Bi-weekly poll check skipped because "
            "BIWEEKLY_TOPIC_ID is not configured."
        )
        return 0

    current_date = datetime.now(
        SINGAPORE_TIMEZONE
    ).date()

    pending_events = get_pending_biweekly_events(
        current_date=current_date
    )

    sent_count = 0

    for event in pending_events:
        event_date_text = event.event_date.strftime(
            "%d-%m-%Y"
        )

        await post_biweekly_poll(
            bot=context.bot,
            chat_id=BIWEEKLY_CHAT_ID,
            event_date_text=event_date_text,
            message_thread_id=BIWEEKLY_TOPIC_ID,
        )

        mark_biweekly_poll_sent(
            event_id=event.id
        )

        sent_count += 1

    if sent_count == 0:
        logger.info(
            "No pending bi-weekly polls were found."
        )

    return sent_count


async def run_biweekly_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Run the automatic bi-weekly poll check manually."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    if BIWEEKLY_CHAT_ID is None:
        await message.reply_text(
            "❌ BIWEEKLY_CHAT_ID is not configured."
        )
        return

    if BIWEEKLY_TOPIC_ID is None:
        await message.reply_text(
            "❌ BIWEEKLY_TOPIC_ID is not configured."
        )
        return

    await message.reply_text(
        "🔍 Running the automatic bi-weekly poll check..."
    )

    sent_count = await send_scheduled_biweekly_polls(
        context
    )

    if sent_count == 0:
        await message.reply_text(
            "✅ Check completed.\n\n"
            "No pending bi-weekly polls were found."
        )
        return

    await message.reply_text(
        "✅ Check completed.\n\n"
        f"Bi-weekly polls sent: {sent_count}"
    )


def register_biweekly_handlers(
    application: Application,
) -> None:
    """Register bi-weekly commands and the optional scheduler."""

    application.add_handler(
        CommandHandler(
            "createbiweekly",
            create_biweekly_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "listbiweekly",
            list_biweekly_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "sendbiweekly",
            send_biweekly_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "testbiweekly",
            send_biweekly_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runbiweeklycheck",
            run_biweekly_check_command,
        )
    )

    if not BIWEEKLY_SCHEDULER_ENABLED:
        logger.info(
            "Automatic bi-weekly polls are disabled."
        )
        return

    if BIWEEKLY_CHAT_ID is None:
        logger.warning(
            "Bi-weekly scheduler was not started because "
            "BIWEEKLY_CHAT_ID is missing."
        )
        return

    if BIWEEKLY_TOPIC_ID is None:
        logger.warning(
            "Bi-weekly scheduler was not started because "
            "BIWEEKLY_TOPIC_ID is missing."
        )
        return

    if application.job_queue is None:
        raise RuntimeError(
            "Telegram JobQueue is unavailable. "
            'Install "python-telegram-bot[job-queue]".'
        )

    application.job_queue.run_daily(
        callback=send_scheduled_biweekly_polls,
        time=time(
            hour=20,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        name="daily-biweekly-poll-check",
    )

    logger.info(
        "Bi-weekly poll check scheduled for "
        "8:00 PM Singapore time, topic %s.",
        BIWEEKLY_TOPIC_ID,
    )