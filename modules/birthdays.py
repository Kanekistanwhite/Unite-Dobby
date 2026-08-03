import logging
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config.settings import (
    BIRTHDAY_CHAT_ID,
    BIRTHDAY_PLANNING_CHAT_ID,
    BIRTHDAY_PLANNING_SCHEDULER_ENABLED,
    BIRTHDAY_SCHEDULER_ENABLED,
    BIRTHDAY_TOPIC_ID,
)
from services.birthday_planning_service import (
    BirthdayPlanningMember,
    get_birthday_planning_member_by_name,
    get_birthday_planning_reminders_for_date,
    get_next_birthday_date,
)
from services.birthday_service import (
    get_birthday_member_by_name,
    get_birthdays_for_date,
)
from services.date_service import format_full_date
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)

SINGAPORE_TIMEZONE = ZoneInfo("Asia/Singapore")


def build_birthday_message(
    display_name: str,
) -> str:
    """Build the public birthday greeting."""

    return (
        f"🎉 HAPPY BIRTHDAY, {display_name.upper()}! 🥳🎂\n\n"
        f"Everyone, let’s show {display_name} some birthday love "
        f"today! UNITE loves you so much❤️\n\n"
        "Have an amazing and blessed year ahead! 🙌"
    )


def build_birthday_planning_message(
    member: BirthdayPlanningMember,
    birthday_date: date,
    reminder_type: str,
) -> str:
    """Build a private birthday-planning reminder."""

    formatted_date = format_full_date(
        birthday_date
    )

    if reminder_type == "month":
        return (
            "🎂 BIRTHDAY PLANNING REMINDER\n\n"
            f"👤 Upcoming Birthday: {member.display_name}\n"
            f"📅 {formatted_date}\n"
            f"🙋 Assigned PIC: {member.planner_name}\n"
            "⏳ 1 month to go\n\n"
            "Please create the birthday planning chat "
            "and begin planning:\n\n"
            "🎁 Gift\n"
            "🎂 Cake or food\n"
            "💌 Birthday message\n"
            "🎉 Celebration plan\n"
            "💰 Budget"
        )

    if reminder_type == "fortnight":
        return (
            "⏰ BIRTHDAY PLANNING FOLLOW-UP\n\n"
            f"{member.display_name}’s birthday is coming up "
            "in 2 weeks!\n\n"
            f"📅 {formatted_date}\n"
            f"🙋 Assigned PIC: {member.planner_name}\n\n"
            "Please confirm that everything is settled:\n\n"
            "✅ Gift\n"
            "✅ Cake or food\n"
            "✅ Birthday message\n"
            "✅ Celebration plan\n"
            "✅ Budget"
        )

    raise ValueError(
        "Reminder type must be 'month' or 'fortnight'."
    )


def leader_is_approved(
    update: Update,
) -> bool:
    """Check whether the person is an approved leader."""

    user = update.effective_user
    user_id = user.id if user else None

    return is_approved_leader(user_id)


async def post_birthday_greeting(
    bot: Bot,
    chat_id: int,
    display_name: str,
    message_thread_id: int | None = None,
) -> None:
    """Send one public birthday greeting."""

    await bot.send_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        text=build_birthday_message(
            display_name=display_name,
        ),
    )

    logger.info(
        "Birthday greeting sent for %s to chat %s, topic %s.",
        display_name,
        chat_id,
        message_thread_id,
    )


async def post_birthday_planning_reminder(
    bot: Bot,
    chat_id: int,
    member: BirthdayPlanningMember,
    birthday_date: date,
    reminder_type: str,
) -> None:
    """Send one reminder to the private planning group."""

    message = build_birthday_planning_message(
        member=member,
        birthday_date=birthday_date,
        reminder_type=reminder_type,
    )

    await bot.send_message(
        chat_id=chat_id,
        text=message,
    )

    logger.info(
        "Birthday planning reminder sent for %s to chat %s.",
        member.display_name,
        chat_id,
    )


async def send_daily_birthday_greetings(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Check today's birthdays and send public greetings."""

    if BIRTHDAY_CHAT_ID is None:
        logger.warning(
            "Birthday greeting skipped because "
            "BIRTHDAY_CHAT_ID is not configured."
        )
        return 0

    today = datetime.now(
        SINGAPORE_TIMEZONE
    ).date()

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
        return 0

    for display_name, _telegram_username in birthdays:
        await post_birthday_greeting(
            bot=context.bot,
            chat_id=BIRTHDAY_CHAT_ID,
            display_name=display_name,
            message_thread_id=BIRTHDAY_TOPIC_ID,
        )

    return len(birthdays)


async def send_daily_birthday_planning_reminders(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Send private reminders that are due today."""

    if BIRTHDAY_PLANNING_CHAT_ID is None:
        logger.warning(
            "Birthday planning check skipped because "
            "BIRTHDAY_PLANNING_CHAT_ID is not configured."
        )
        return 0

    today = datetime.now(
        SINGAPORE_TIMEZONE
    ).date()

    reminders = get_birthday_planning_reminders_for_date(
        reference_date=today
    )

    for reminder in reminders:
        await post_birthday_planning_reminder(
            bot=context.bot,
            chat_id=BIRTHDAY_PLANNING_CHAT_ID,
            member=reminder.member,
            birthday_date=reminder.birthday_date,
            reminder_type=reminder.reminder_type,
        )

    if not reminders:
        logger.info(
            "No birthday planning reminders are due today."
        )

    return len(reminders)


async def test_birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show a birthday-message preview."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    member_name = " ".join(
        context.args
    ).strip()

    if not member_name:
        await message.reply_text(
            "Usage:\n"
            "/testbirthday Member Name\n\n"
            "Example:\n"
            "/testbirthday Kelly"
        )
        return

    member = get_birthday_member_by_name(
        member_name
    )

    if member is None:
        await message.reply_text(
            f"❌ Member '{member_name}' was not found."
        )
        return

    display_name, _telegram_username = member

    await message.reply_text(
        "🧪 Birthday greeting preview\n\n"
        + build_birthday_message(
            display_name=display_name,
        )
    )


async def send_birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send a birthday greeting into the current chat or topic."""

    message = update.effective_message
    chat = update.effective_chat

    if message is None or chat is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    member_name = " ".join(
        context.args
    ).strip()

    if not member_name:
        await message.reply_text(
            "Usage:\n"
            "/sendbirthday Member Name\n\n"
            "Example:\n"
            "/sendbirthday Kelly"
        )
        return

    member = get_birthday_member_by_name(
        member_name
    )

    if member is None:
        await message.reply_text(
            f"❌ Member '{member_name}' was not found."
        )
        return

    display_name, _telegram_username = member

    await post_birthday_greeting(
        bot=context.bot,
        chat_id=chat.id,
        display_name=display_name,
        message_thread_id=message.message_thread_id,
    )


async def run_birthday_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Test the configured public birthday destination."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    if BIRTHDAY_CHAT_ID is None:
        await message.reply_text(
            "❌ BIRTHDAY_CHAT_ID is not configured."
        )
        return

    member_name = " ".join(
        context.args
    ).strip()

    if member_name:
        member = get_birthday_member_by_name(
            member_name
        )

        if member is None:
            await message.reply_text(
                f"❌ Member '{member_name}' was not found."
            )
            return

        display_name, _telegram_username = member

        destination_description = (
            f"topic {BIRTHDAY_TOPIC_ID}"
            if BIRTHDAY_TOPIC_ID is not None
            else "the main group chat"
        )

        await message.reply_text(
            "🔍 Testing the configured birthday destination...\n\n"
            f"Destination: {destination_description}"
        )

        await post_birthday_greeting(
            bot=context.bot,
            chat_id=BIRTHDAY_CHAT_ID,
            display_name=display_name,
            message_thread_id=BIRTHDAY_TOPIC_ID,
        )

        await message.reply_text(
            "✅ Birthday greeting sent to the configured destination."
        )
        return

    await message.reply_text(
        "🔍 Running today’s automatic birthday check..."
    )

    greetings_sent = await send_daily_birthday_greetings(
        context
    )

    if greetings_sent == 0:
        await message.reply_text(
            "ℹ️ There are no birthdays today."
        )
    else:
        await message.reply_text(
            f"✅ Sent {greetings_sent} birthday greeting(s)."
        )


async def run_birthday_planning_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send a selected reminder to the planning test group."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    if BIRTHDAY_PLANNING_CHAT_ID is None:
        await message.reply_text(
            "❌ BIRTHDAY_PLANNING_CHAT_ID is not configured.\n\n"
            "Add the private planning-group chat ID "
            "to Railway Variables."
        )
        return

    if len(context.args) < 2:
        await message.reply_text(
            "Usage:\n"
            "/runbirthdayplanning Member Name month\n"
            "/runbirthdayplanning Member Name fortnight\n\n"
            "Examples:\n"
            "/runbirthdayplanning Kelly month\n"
            "/runbirthdayplanning Grace Ee fortnight"
        )
        return

    reminder_keyword = context.args[-1].strip().lower()

    reminder_aliases = {
        "month": "month",
        "1month": "month",
        "one-month": "month",
        "fortnight": "fortnight",
        "2weeks": "fortnight",
        "two-weeks": "fortnight",
    }

    reminder_type = reminder_aliases.get(
        reminder_keyword
    )

    if reminder_type is None:
        await message.reply_text(
            "❌ The reminder type must be "
            "'month' or 'fortnight'."
        )
        return

    member_name = " ".join(
        context.args[:-1]
    ).strip()

    member = get_birthday_planning_member_by_name(
        member_name
    )

    if member is None:
        await message.reply_text(
            f"❌ Member '{member_name}' or their planner "
            "was not found."
        )
        return

    today = datetime.now(
        SINGAPORE_TIMEZONE
    ).date()

    birthday_date = get_next_birthday_date(
        birthday_day=member.birthday_day,
        birthday_month=member.birthday_month,
        reference_date=today,
    )

    await message.reply_text(
        "🔍 Sending the birthday-planning reminder "
        "to the configured private group..."
    )

    await post_birthday_planning_reminder(
        bot=context.bot,
        chat_id=BIRTHDAY_PLANNING_CHAT_ID,
        member=member,
        birthday_date=birthday_date,
        reminder_type=reminder_type,
    )

    await message.reply_text(
        "✅ Birthday-planning reminder sent."
    )


async def run_birthday_planning_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Run today's planning-reminder check manually."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    if BIRTHDAY_PLANNING_CHAT_ID is None:
        await message.reply_text(
            "❌ BIRTHDAY_PLANNING_CHAT_ID is not configured."
        )
        return

    await message.reply_text(
        "🔍 Checking for birthday-planning reminders due today..."
    )

    reminder_count = (
        await send_daily_birthday_planning_reminders(
            context
        )
    )

    if reminder_count == 0:
        await message.reply_text(
            "ℹ️ No birthday-planning reminders are due today."
        )
    else:
        await message.reply_text(
            f"✅ Sent {reminder_count} planning reminder(s)."
        )


def register_birthday_handlers(
    application: Application,
) -> None:
    """Register birthday commands and optional schedulers."""

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

    application.add_handler(
        CommandHandler(
            "runbirthdaycheck",
            run_birthday_check_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runbirthdayplanning",
            run_birthday_planning_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runbirthdayplanningcheck",
            run_birthday_planning_check_command,
        )
    )

    schedulers_requested = (
        BIRTHDAY_SCHEDULER_ENABLED
        or BIRTHDAY_PLANNING_SCHEDULER_ENABLED
    )

    if schedulers_requested and application.job_queue is None:
        raise RuntimeError(
            "Telegram JobQueue is unavailable. "
            'Install "python-telegram-bot[job-queue]".'
        )

    if not BIRTHDAY_SCHEDULER_ENABLED:
        logger.info(
            "Automatic birthday greetings are disabled."
        )

    elif BIRTHDAY_CHAT_ID is None:
        logger.warning(
            "Birthday scheduler was not started because "
            "BIRTHDAY_CHAT_ID is missing."
        )

    else:
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
            "12:00 AM Singapore time, topic %s.",
            BIRTHDAY_TOPIC_ID,
        )

    if not BIRTHDAY_PLANNING_SCHEDULER_ENABLED:
        logger.info(
            "Automatic birthday-planning reminders are disabled."
        )

    elif BIRTHDAY_PLANNING_CHAT_ID is None:
        logger.warning(
            "Birthday-planning scheduler was not started because "
            "BIRTHDAY_PLANNING_CHAT_ID is missing."
        )

    else:
        application.job_queue.run_daily(
            callback=send_daily_birthday_planning_reminders,
            time=time(
                hour=10,
                minute=0,
                tzinfo=SINGAPORE_TIMEZONE,
            ),
            name="daily-birthday-planning-reminders",
        )

        logger.info(
            "Birthday-planning reminder check scheduled for "
            "10:00 AM Singapore time."
        )