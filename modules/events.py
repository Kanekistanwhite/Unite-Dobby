from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config.settings import EVENTS_LEADER_USER_IDS
from services.events_service import (
    cancel_events_item,
    complete_deadline,
    create_events_item,
    get_upcoming_events_items,
)


def is_events_leader(
    user_id: int | None,
) -> bool:
    """Check whether a Telegram user can manage Events Team."""

    if user_id is None:
        return False

    return user_id in EVENTS_LEADER_USER_IDS


async def check_events_permission(
    update: Update,
) -> bool:
    """Allow only approved Events Team leaders."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return False

    user_id = user.id if user else None

    if not is_events_leader(user_id):
        await message.reply_text(
            "⛔ This command is only available "
            "to approved Events Team leaders."
        )
        return False

    return True


def format_events_datetime(
    item_type: str,
    scheduled_at: datetime,
) -> str:
    """Format an Events Team date nicely."""

    date_text = scheduled_at.strftime(
        "%A, %-d %B %Y"
    )

    if item_type == "meeting":
        time_text = scheduled_at.strftime(
            "%-I:%M %p"
        )

        return (
            f"{date_text}\n"
            f"🕗 {time_text}"
        )

    return date_text


async def add_event_meeting_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Add an Events Team meeting.

    Format:
    /addeventmeeting DD-MM-YYYY HH:MM | Title
    """

    if not await check_events_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    command_text = message.text or ""

    try:
        details = command_text.split(
            " ",
            maxsplit=1,
        )[1]
    except IndexError:
        await message.reply_text(
            "Usage:\n"
            "/addeventmeeting DD-MM-YYYY HH:MM | Meeting Name\n\n"
            "Example:\n"
            "/addeventmeeting 18-09-2026 20:00 | "
            "September Planning Meeting"
        )
        return

    parts = [
        part.strip()
        for part in details.split(
            "|",
            maxsplit=1,
        )
    ]

    if len(parts) != 2:
        await message.reply_text(
            "Please use:\n"
            "/addeventmeeting DD-MM-YYYY HH:MM | Meeting Name"
        )
        return

    datetime_text = parts[0]
    title = parts[1]

    try:
        scheduled_at = datetime.strptime(
            datetime_text,
            "%d-%m-%Y %H:%M",
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid date or time.\n\n"
            "Please use:\n"
            "DD-MM-YYYY HH:MM\n\n"
            "Example:\n"
            "18-09-2026 20:00"
        )
        return

    if scheduled_at <= datetime.now():
        await message.reply_text(
            "❌ The meeting must be scheduled in the future."
        )
        return

    try:
        item = create_events_item(
            item_type="meeting",
            title=title,
            scheduled_at=scheduled_at,
        )
    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    await message.reply_text(
        "✅ EVENTS MEETING ADDED\n\n"
        f"🆔 #{item.id}\n"
        f"📅 {item.title}\n"
        f"{format_events_datetime('meeting', item.scheduled_at)}"
    )


async def add_event_deadline_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Add an Events Team deadline.

    Format:
    /addeventdeadline DD-MM-YYYY | Title
    """

    if not await check_events_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    command_text = message.text or ""

    try:
        details = command_text.split(
            " ",
            maxsplit=1,
        )[1]
    except IndexError:
        await message.reply_text(
            "Usage:\n"
            "/addeventdeadline DD-MM-YYYY | Deadline Name\n\n"
            "Example:\n"
            "/addeventdeadline 25-09-2026 | "
            "Finalise Camp Games Proposal"
        )
        return

    parts = [
        part.strip()
        for part in details.split(
            "|",
            maxsplit=1,
        )
    ]

    if len(parts) != 2:
        await message.reply_text(
            "Please use:\n"
            "/addeventdeadline DD-MM-YYYY | Deadline Name"
        )
        return

    date_text = parts[0]
    title = parts[1]

    try:
        scheduled_at = datetime.strptime(
            date_text,
            "%d-%m-%Y",
        ).replace(
            hour=9,
            minute=0,
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid date.\n\n"
            "Please use:\n"
            "DD-MM-YYYY\n\n"
            "Example:\n"
            "25-09-2026"
        )
        return

    try:
        item = create_events_item(
            item_type="deadline",
            title=title,
            scheduled_at=scheduled_at,
        )
    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    await message.reply_text(
        "✅ EVENTS DEADLINE ADDED\n\n"
        f"🆔 #{item.id}\n"
        f"⏰ {item.title}\n"
        f"📅 {format_events_datetime('deadline', item.scheduled_at)}"
    )


async def events_schedule_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show upcoming Events Team meetings and deadlines."""

    if not await check_events_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    items = get_upcoming_events_items()

    if not items:
        await message.reply_text(
            "📋 EVENTS TEAM SCHEDULE\n\n"
            "Nothing upcoming at the moment."
        )
        return

    sections: list[str] = []

    for item in items:
        if item.item_type == "meeting":
            icon = "📅"
            type_name = "Meeting"
        else:
            icon = "⏰"
            type_name = "Deadline"

        status = ""

        if item.is_completed:
            status = "\n✅ Completed"

        sections.append(
            f"#{item.id} {icon} {item.title}\n"
            f"{type_name}\n"
            f"{format_events_datetime(item.item_type, item.scheduled_at)}"
            f"{status}"
        )

    await message.reply_text(
        "📋 EVENTS TEAM — UPCOMING\n\n"
        + "\n\n".join(sections)
    )


async def complete_event_deadline_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Complete a deadline using /completeevent ID."""

    if not await check_events_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:
        await message.reply_text(
            "Usage:\n"
            "/completeevent ID\n\n"
            "Example:\n"
            "/completeevent 3"
        )
        return

    try:
        item_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "❌ The ID must be a number."
        )
        return

    try:
        item = complete_deadline(
            item_id
        )
    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    await message.reply_text(
        "✅ DEADLINE COMPLETED\n\n"
        f"#{item.id} — {item.title}"
    )


async def cancel_event_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Cancel an Events Team meeting or deadline."""

    if not await check_events_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:
        await message.reply_text(
            "Usage:\n"
            "/cancelevent ID\n\n"
            "Example:\n"
            "/cancelevent 4"
        )
        return

    try:
        item_id = int(
            context.args[0]
        )
    except ValueError:
        await message.reply_text(
            "❌ The ID must be a number."
        )
        return

    try:
        item = cancel_events_item(
            item_id
        )
    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    await message.reply_text(
        "❌ EVENTS ITEM CANCELLED\n\n"
        f"#{item.id} — {item.title}"
    )


def register_events_handlers(
    application: Application,
) -> None:
    """Register Events Team commands."""

    application.add_handler(
        CommandHandler(
            "addeventmeeting",
            add_event_meeting_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "addeventdeadline",
            add_event_deadline_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "eventschedule",
            events_schedule_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "completeevent",
            complete_event_deadline_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "cancelevent",
            cancel_event_command,
        )
    )