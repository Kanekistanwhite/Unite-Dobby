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
    EVENTS_CHAT_ID,
    EVENTS_LEADER_USER_IDS,
    EVENTS_SCHEDULER_ENABLED,
    EVENTS_TOPIC_ID,
)
from services.events_service import (
    cancel_events_item,
    complete_deadline,
    create_events_item,
    get_events_items_for_reminders,
    get_singapore_now,
    get_upcoming_events_items,
    mark_events_reminder_sent,
)


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


def is_events_leader(
    user_id: int | None,
) -> bool:
    """Check whether a user can manage Events Team."""

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

    user_id = (
        user.id
        if user
        else None
    )

    if not is_events_leader(
        user_id
    ):
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

    date_text = (
        f"{scheduled_at.strftime('%A')}, "
        f"{scheduled_at.day} "
        f"{scheduled_at.strftime('%B %Y')}"
    )

    if item_type == "meeting":
        time_text = scheduled_at.strftime(
            "%I:%M %p"
        ).lstrip("0")

        return (
            f"{date_text}\n"
            f"🕗 {time_text}"
        )

    return date_text


async def add_event_meeting_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add an Events Team meeting."""

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
            "DD-MM-YYYY HH:MM"
        )
        return

    if scheduled_at <= get_singapore_now():
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
        f"{format_events_datetime('meeting', item.scheduled_at)}\n\n"
        "🔔 Reminders:\n"
        "• 1 week before — 10:00 AM\n"
        "• 1 day before — 10:00 AM"
    )


async def add_event_deadline_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add an Events Team deadline."""

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
            "Finalise Event Proposal"
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
            hour=10,
            minute=0,
        )
    except ValueError:
        await message.reply_text(
            "❌ Invalid date.\n\n"
            "Please use DD-MM-YYYY."
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
        f"📅 {format_events_datetime('deadline', item.scheduled_at)}\n\n"
        "🔔 Reminders:\n"
        "• 3 days before — 10:00 AM\n"
        "• Deadline day — 10:00 AM"
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
    """Complete a deadline."""

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
        f"#{item.id} — {item.title}\n\n"
        "Dobby will no longer send reminders "
        "for this deadline."
    )


async def cancel_event_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Cancel a meeting or deadline."""

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
        f"#{item.id} — {item.title}\n\n"
        "Dobby will no longer send reminders "
        "for this item."
    )


async def send_events_reminders(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Check all Events items and send reminders that are due."""

    if EVENTS_CHAT_ID is None:
        logger.error(
            "EVENTS_CHAT_ID is not configured."
        )
        return 0

    now = get_singapore_now()
    today = now.date()

    items = get_events_items_for_reminders()

    sent_count = 0

    thread_kwargs = {}

    if EVENTS_TOPIC_ID is not None:
        thread_kwargs[
            "message_thread_id"
        ] = EVENTS_TOPIC_ID

    for item in items:

        if item.is_completed:
            continue

        days_until = (
            item.scheduled_at.date()
            - today
        ).days

        reminder_type = None
        reminder_text = None

        if item.item_type == "meeting":

            if (
                days_until == 7
                and not item.reminder_3d_sent
            ):
                reminder_type = "meeting_week"

                reminder_text = (
                    "📣 EVENTS TEAM MEETING REMINDER\n\n"
                    f"📅 {item.title}\n"
                    f"🗓 {format_events_datetime('meeting', item.scheduled_at)}\n\n"
                    "⏳ 1 week to go!"
                )

            elif (
                days_until == 1
                and not item.reminder_1d_sent
            ):
                reminder_type = "meeting_day"

                reminder_text = (
                    "📣 EVENTS TEAM MEETING REMINDER\n\n"
                    f"📅 {item.title}\n"
                    f"🗓 {format_events_datetime('meeting', item.scheduled_at)}\n\n"
                    "⏳ Meeting is tomorrow!"
                )

        elif item.item_type == "deadline":

            if (
                days_until == 3
                and not item.reminder_3d_sent
            ):
                reminder_type = "deadline_3d"

                reminder_text = (
                    "⏰ EVENTS TEAM DEADLINE REMINDER\n\n"
                    f"📌 {item.title}\n"
                    f"📅 Due: "
                    f"{format_events_datetime('deadline', item.scheduled_at)}\n\n"
                    "⏳ 3 days left!"
                )

            elif (
                days_until == 0
                and not item.deadline_day_sent
            ):
                reminder_type = "deadline_day"

                reminder_text = (
                    "🚨 EVENTS TEAM DEADLINE TODAY\n\n"
                    f"📌 {item.title}\n\n"
                    "⏰ This deadline is due today."
                )

        if (
            reminder_type is None
            or reminder_text is None
        ):
            continue

        try:
            await context.bot.send_message(
                chat_id=EVENTS_CHAT_ID,
                text=reminder_text,
                **thread_kwargs,
            )

            mark_events_reminder_sent(
                item.id,
                reminder_type,
            )

            sent_count += 1

            logger.info(
                "Sent Events reminder %s for item #%s.",
                reminder_type,
                item.id,
            )

        except Exception:
            logger.exception(
                "Failed to send Events reminder "
                "for item #%s.",
                item.id,
            )

    return sent_count


async def scheduled_events_reminder_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Run the automatic Events reminder check."""

    logger.info(
        "Running Events Team reminder check."
    )

    sent_count = await send_events_reminders(
        context
    )

    logger.info(
        "Events reminder check finished. "
        "%s reminder(s) sent.",
        sent_count,
    )


async def run_events_reminder_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Manually run the Events reminder check."""

    if not await check_events_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    sent_count = await send_events_reminders(
        context
    )

    if sent_count == 0:
        await message.reply_text(
            "🔔 Events reminder check complete.\n\n"
            "No reminders are due today."
        )
    else:
        await message.reply_text(
            "✅ Events reminder check complete.\n\n"
            f"{sent_count} reminder(s) sent."
        )


def register_events_handlers(
    application: Application,
) -> None:
    """Register Events Team commands and reminder scheduler."""

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

    application.add_handler(
        CommandHandler(
            "runeventscheck",
            run_events_reminder_check_command,
        )
    )

    if not EVENTS_SCHEDULER_ENABLED:
        logger.info(
            "Events scheduler is disabled."
        )
        return

    if application.job_queue is None:
        logger.error(
            "JobQueue is unavailable. "
            "Events scheduler was not started."
        )
        return

    application.job_queue.run_daily(
        scheduled_events_reminder_job,
        time=time(
            hour=10,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        name="events_team_reminder_check",
    )

    logger.info(
        "Events scheduler enabled: "
        "daily at 10:00 AM Singapore time."
    )