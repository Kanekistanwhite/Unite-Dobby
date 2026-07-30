import logging

from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from services.biweekly_service import (
    create_biweekly_event,
    get_biweekly_event_by_date,
    get_upcoming_biweekly_events,
)
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

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

    event = get_biweekly_event_by_date(event_date_text)

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
        allows_revoting=True,
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

    event_date_text = " ".join(context.args).strip()

    if not event_date_text:
        await update.message.reply_text(
            "Usage:\n"
            "/createbiweekly DD-MM-YYYY\n\n"
            "Example:\n"
            "/createbiweekly 15-08-2026"
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
    """
    Send a real bi-weekly poll into the current chat.

    During development, use this only in the private test group.
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

    event_date_text = " ".join(context.args).strip()

    if not event_date_text:
        await update.message.reply_text(
            "Usage:\n"
            "/sendbiweekly DD-MM-YYYY\n\n"
            "Example:\n"
            "/sendbiweekly 15-08-2026"
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


def register_biweekly_handlers(
    application: Application,
) -> None:
    """Register bi-weekly event commands."""

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

    # Keep the previous test command available.
    application.add_handler(
        CommandHandler(
            "testbiweekly",
            send_biweekly_command,
        )
    )