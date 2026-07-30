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
)
from services.biweekly_service import (
    create_biweekly_event,
    get_biweekly_event_by_date,
    get_pending_biweekly_events,
    get_upcoming_biweekly_events,
    mark_biweekly_poll_sent,
)
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo("Asia/Singapore")

BIWEEKLY_POLL_OPTIONS = [
    "Lunch",
    "Dinner",
    "CMI Both",
]


def leader_is_approved(update: Update) -> bool:
    """Check whether the command user is an approved leader."""

    user = update.effective_user
    user_id = user.id if user else None

    return is_approved_leader(user_id)


async def post_biweekly_poll(
    bot: Bot,
    chat_id: int,
    event_date_text: str,
) -> None:
    """Post a bi-weekly attendance poll."""

    event = get_biweekly_event_by_date(
        event_date_text
    )

    if event is None:
        raise ValueError(
            f"No bi-weekly event exists on {event_date_text}."
        )

    formatted_date = event.event_date.strftime(
        "%d %B %Y"
    )

    await bot.send_message(
        chat_id=chat_id,
        text=(
            "🍽️ Bi-weekly Attendance\n\n"
            f"Meetup date: {formatted_date}\n\n"
            "Select every timing you can attend.\n"
            "Choose CMI Both only if you cannot attend "
            "either timing."
        ),
    )

    await bot.send_poll(
        chat_id=chat_id,
        question=f"Attendance for {formatted_date}",
        options=BIWEEKLY_POLL_OPTIONS,
        is_anonymous=False,
        allows_multiple_answers=True,
    )

    logger.info(
        "Bi-weekly poll for %s sent to chat %s.",
        event_date_text,
        chat_id,
    )


async def create_biweekly_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Create an event using /createbiweekly DD-MM-YYYY."""

    if update.message is None:
        return

    if not leader_is_approved(update):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    event_date_text = " ".join(
        context.args
    ).strip()

    if not event_date_text:
        await update.message.reply_text(
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
        await update.message.reply_text(
            f"❌ {error}"
        )
        return

    await update.message.reply_text(
        "✅ Bi-weekly event created\n\n"
        f"Meetup date: "
        f"{event.event_date.strftime('%d-%m-%Y')}\n"
        f"Poll date: "
        f"{event.poll_date.strftime('%d-%m-%Y')}\n\n"
        "The poll will be scheduled 10 days "
        "before the meetup."
    )


async def list_biweekly_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """List upcoming bi-weekly events."""

    if update.message is None:
        return

    if not leader_is_approved(update):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    events = get_upcoming_biweekly_events()

    if not events:
        await update.message.reply_text(
            "There are no upcoming bi-weekly events."
        )
        return

    event_lines = []

    for number, event in enumerate(
        events,
        start=1,
    ):
        poll_status = (
            "Sent"
            if event.poll_sent
            else "Not sent"
        )

        event_lines.append(
            f"{number}. "
            f"{event.event_date.strftime('%d-%m-%Y')}\n"
            f"   Poll date: "
            f"{event.poll_date.strftime('%d-%m-%Y')}\n"
            f"   Poll status: {poll_status}"
        )

    await update.message.reply_text(
        "📅 Upcoming Bi-weekly Events\n\n"
        + "\n\n".join(event_lines)
    )


async def send_biweekly_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send a bi-weekly poll into the current chat."""

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

    event_date_text = " ".join(
        context.args
    ).strip()

    if not event_date_text:
        await update.message.reply_text(
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
        )

    except ValueError as error:
        await update.message.reply_text(
            f"❌ {error}"
        )


async def send_scheduled_biweekly_polls(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Check for due bi-weekly polls and send them once."""

    if BIWEEKLY_CHAT_ID is None:
        logger.warning(
            "Bi-weekly poll skipped because "
            "BIWEEKLY_CHAT_ID is not configured."
        )
        return 0

    current_date = datetime.now(
        SINGAPORE_TIMEZONE
    ).date()

    events = get_pending_biweekly_events(
        current_date
    )

    if not events:
        logger.info(
            "No pending bi-weekly polls for %s.",
            current_date,
        )
        return 0

    sent_count = 0

    for event in events:
        event_date_text = event.event_date.strftime(
            "%d-%m-%Y"
        )

        try:
            await post_biweekly_poll(
                bot=context.bot,
                chat_id=BIWEEKLY_CHAT_ID,
                event_date_text=event_date_text,
            )

            mark_biweekly_poll_sent(
                event.id
            )

            sent_count += 1

            logger.info(
                "Automatic bi-weekly poll sent for %s.",
                event_date_text,
            )

        except Exception:
            logger.exception(
                "Automatic bi-weekly poll failed for %s.",
                event_date_text,
            )

    return sent_count


async def run_biweekly_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Run the automatic bi-weekly check immediately."""

    if update.message is None:
        return

    if not leader_is_approved(update):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    if BIWEEKLY_CHAT_ID is None:
        await update.message.reply_text(
            "❌ BIWEEKLY_CHAT_ID is not configured.\n\n"
            "Add your private test-group chat ID to the .env file."
        )
        return

    await update.message.reply_text(
        "🔍 Running the automatic bi-weekly poll check..."
    )

    sent_count = await send_scheduled_biweekly_polls(
        context
    )

    if sent_count == 0:
        await update.message.reply_text(
            "✅ Check completed.\n\n"
            "No pending bi-weekly polls were found."
        )
        return

    await update.message.reply_text(
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
        "8:00 PM Singapore time."
    )