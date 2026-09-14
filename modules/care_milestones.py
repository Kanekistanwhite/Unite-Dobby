import logging
from datetime import (
    date,
    time,
    timedelta,
)
from zoneinfo import ZoneInfo

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config.settings import (
    CARE_LEADER_USER_IDS,
    CARE_MILESTONE_CHAT_ID,
    CARE_MILESTONE_SCHEDULER_ENABLED,
    CARE_MILESTONE_TOPIC_ID,
)
from services.care_milestone_service import (
    MILESTONE_CHECKLIST,
    add_milestone,
    annual_plan_flag_is_set,
    build_annual_lookout_reminder,
    build_one_month_reminder,
    build_two_week_reminder,
    cancel_milestone,
    format_active_milestones,
    format_milestone,
    format_milestone_annual_plan,
    format_milestone_history,
    format_month_milestones,
    format_year_milestones,
    get_active_milestones,
    get_milestone,
    get_or_create_milestone_annual_plan,
    get_singapore_today,
    mark_annual_plan_flag,
    mark_planning_reminder_sent,
    milestone_reminder_was_sent,
    previous_month_first_day,
    record_milestone_reminder_sent,
    set_milestone_gift,
    subtract_one_calendar_month,
    toggle_milestone_checklist_item,
    toggle_milestone_lookout_item,
    update_milestone_date,
)


logger = logging.getLogger(
    __name__
)

SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


# =========================================================
# PERMISSION
# =========================================================

def is_care_leader(
    user_id: int | None,
) -> bool:
    """Check CARE permission."""

    if user_id is None:
        return False

    return (
        user_id
        in CARE_LEADER_USER_IDS
    )


async def check_care_permission(
    update: Update,
) -> bool:
    """Allow only CARE leaders."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return False

    user_id = (
        user.id
        if user
        else None
    )

    if not is_care_leader(
        user_id
    ):

        await message.reply_text(
            "⛔ This command is only available "
            "to approved CARE Team leaders."
        )

        return False

    return True


# =========================================================
# MILESTONE CHECKLIST KEYBOARD
# =========================================================

def build_milestone_keyboard(
    milestone_id: int,
) -> InlineKeyboardMarkup:
    """Interactive Gift/Card milestone checklist."""

    milestone = get_milestone(
        milestone_id
    )

    if milestone is None:

        return InlineKeyboardMarkup(
            []
        )

    labels = {
        "giftprep": "🎁 Gift Prepared",
        "cardprep": "💌 Card Prepared",
        "giftgiven": "🎁 Gift Given",
        "cardgiven": "💌 Card Given",
    }

    keyboard = []

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in MILESTONE_CHECKLIST.items():

        completed = getattr(
            milestone,
            field_name,
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    (
                        f"{'✅' if completed else '⬜'} "
                        f"{labels[item_key]}"
                    ),
                    callback_data=(
                        f"caremilestone:toggle:"
                        f"{milestone_id}:{item_key}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# ANNUAL PLAN KEYBOARD
# =========================================================

def build_annual_plan_keyboard(
    target_year: int,
) -> InlineKeyboardMarkup:
    """Build annual lookout checklist."""

    plan = get_or_create_milestone_annual_plan(
        target_year
    )

    items = [
        (
            "leaders",
            "cell_leaders_contacted",
            "📣 Cell Leaders Contacted",
        ),
        (
            "responses",
            "responses_collected",
            "📥 Responses Collected",
        ),
        (
            "entered",
            "known_milestones_entered",
            "📝 Milestones Entered",
        ),
    ]

    keyboard = []

    for (
        item_key,
        field_name,
        label,
    ) in items:

        done = getattr(
            plan,
            field_name,
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{'✅' if done else '⬜'} {label}",
                    callback_data=(
                        "caremilestone:lookout:"
                        f"{target_year}:{item_key}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# SEND MESSAGE TO MILESTONE TOPIC
# =========================================================

async def send_care_milestone_message(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> bool:
    """Send message to CARE Milestone topic."""

    if CARE_MILESTONE_CHAT_ID is None:

        logger.error(
            "CARE_MILESTONE_CHAT_ID is not configured."
        )

        return False

    kwargs = {}

    if CARE_MILESTONE_TOPIC_ID is not None:

        kwargs[
            "message_thread_id"
        ] = CARE_MILESTONE_TOPIC_ID

    try:

        await context.bot.send_message(
            chat_id=CARE_MILESTONE_CHAT_ID,
            text=text,
            **kwargs,
        )

        return True

    except Exception:

        logger.exception(
            "CARE Milestone reminder could not be sent."
        )

        return False


# =========================================================
# AUTOMATIC SCHEDULER
# =========================================================

async def send_due_milestone_reminders(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Send every milestone reminder due today."""

    today = get_singapore_today()

    sent_count = 0

    # -----------------------------------------------------
    # 1 NOVEMBER
    # LOOK OUT FOR NEXT YEAR'S MILESTONES
    # -----------------------------------------------------

    if (
        today.month == 11
        and today.day == 1
    ):

        target_year = (
            today.year + 1
        )

        if not annual_plan_flag_is_set(
            target_year,
            "lookout_open_sent",
        ):

            sent = await send_care_milestone_message(
                context,
                build_annual_lookout_reminder(
                    target_year,
                    followup=False,
                ),
            )

            if sent:

                mark_annual_plan_flag(
                    target_year,
                    "lookout_open_sent",
                )

                sent_count += 1

    # -----------------------------------------------------
    # 15 NOVEMBER
    # FOLLOW UP CELL LEADERS / ANNUAL GIFT PLANNING
    # -----------------------------------------------------

    if (
        today.month == 11
        and today.day == 15
    ):

        target_year = (
            today.year + 1
        )

        if not annual_plan_flag_is_set(
            target_year,
            "lookout_followup_sent",
        ):

            sent = await send_care_milestone_message(
                context,
                build_annual_lookout_reminder(
                    target_year,
                    followup=True,
                ),
            )

            if sent:

                mark_annual_plan_flag(
                    target_year,
                    "lookout_followup_sent",
                )

                sent_count += 1

    # -----------------------------------------------------
    # 1 JANUARY
    # SHOW FULL KNOWN MILESTONE TRACKER
    # -----------------------------------------------------

    if (
        today.month == 1
        and today.day == 1
    ):

        if not annual_plan_flag_is_set(
            today.year,
            "year_start_tracker_sent",
        ):

            text = (
                format_year_milestones(
                    today.year
                )
                + "\n\n"
                "👀 Continue looking out for new milestones "
                "throughout the year and add them to Dobby "
                "whenever they become known."
            )

            sent = await send_care_milestone_message(
                context,
                text,
            )

            if sent:

                mark_annual_plan_flag(
                    today.year,
                    "year_start_tracker_sent",
                )

                sent_count += 1

    # -----------------------------------------------------
    # 1ST OF EVERY MONTH
    # SHOW THIS MONTH'S MILESTONES
    # -----------------------------------------------------

    if today.day == 1:

        reminder_type = "monthly"

        if not milestone_reminder_was_sent(
            today.year,
            today.month,
            reminder_type,
        ):

            text = format_month_milestones(
                today.year,
                today.month,
            )

            sent = await send_care_milestone_message(
                context,
                text,
            )

            if sent:

                record_milestone_reminder_sent(
                    today.year,
                    today.month,
                    reminder_type,
                )

                sent_count += 1

    # -----------------------------------------------------
    # INDIVIDUAL MILESTONE REMINDERS
    # -----------------------------------------------------

    for milestone in get_active_milestones():

        # =================================================
        # EXACT DATE KNOWN
        # =================================================

        if milestone.milestone_date is not None:

            milestone_date = (
                milestone.milestone_date
            )

            # No advance reminders after milestone date.
            if today >= milestone_date:
                continue

            one_month_due = (
                subtract_one_calendar_month(
                    milestone_date
                )
            )

            two_week_due = (
                milestone_date
                - timedelta(
                    days=14
                )
            )

            two_week_type = (
                f"two_week:{milestone.id}"
            )

            two_week_sent = (
                milestone_reminder_was_sent(
                    milestone.milestone_year,
                    milestone.milestone_month,
                    two_week_type,
                )
            )

            # ---------------------------------------------
            # 2 WEEKS BEFORE
            # ---------------------------------------------

            if (
                today >= two_week_due
                and not two_week_sent
            ):

                sent = await send_care_milestone_message(
                    context,
                    build_two_week_reminder(
                        milestone
                    ),
                )

                if sent:

                    record_milestone_reminder_sent(
                        milestone.milestone_year,
                        milestone.milestone_month,
                        two_week_type,
                    )

                    # If the one-month reminder was missed,
                    # consider planning started already.
                    if not milestone.planning_reminder_sent:

                        mark_planning_reminder_sent(
                            milestone.id
                        )

                    sent_count += 1

                continue

            # ---------------------------------------------
            # 1 MONTH BEFORE
            # ---------------------------------------------

            if (
                today >= one_month_due
                and today < two_week_due
                and not milestone.planning_reminder_sent
            ):

                sent = await send_care_milestone_message(
                    context,
                    build_one_month_reminder(
                        milestone
                    ),
                )

                if sent:

                    mark_planning_reminder_sent(
                        milestone.id
                    )

                    sent_count += 1

        # =================================================
        # ONLY MONTH IS KNOWN
        # =================================================

        else:

            first_of_milestone_month = date(
                milestone.milestone_year,
                milestone.milestone_month,
                1,
            )

            planning_due = (
                previous_month_first_day(
                    milestone.milestone_year,
                    milestone.milestone_month,
                )
            )

            if (
                today >= planning_due
                and today < first_of_milestone_month
                and not milestone.planning_reminder_sent
            ):

                sent = await send_care_milestone_message(
                    context,
                    build_one_month_reminder(
                        milestone
                    ),
                )

                if sent:

                    mark_planning_reminder_sent(
                        milestone.id
                    )

                    sent_count += 1

    return sent_count


async def scheduled_milestone_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Automatic daily CARE Milestone check."""

    logger.info(
        "Running CARE Milestone reminder check."
    )

    sent_count = await send_due_milestone_reminders(
        context
    )

    logger.info(
        "CARE Milestone check complete. "
        "%s reminder(s) sent.",
        sent_count,
    )


# =========================================================
# ADD MILESTONE
# =========================================================

async def add_milestone_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add a new milestone."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    raw_text = " ".join(
        context.args
    ).strip()

    parts = [
        part.strip()
        for part in raw_text.split(
            "|"
        )
    ]

    if len(parts) != 3:

        await message.reply_text(
            "Usage:\n"
            "/addmilestone NAME | TYPE | DATE\n\n"
            "Exact date:\n"
            "/addmilestone John Tan | university | "
            "18-05-2027\n\n"
            "Month only:\n"
            "/addmilestone John Tan | university | "
            "05-2027\n\n"
            "Types:\n"
            "secondary\n"
            "polytechnic\n"
            "jc\n"
            "university\n"
            "baptism\n"
            "ord"
        )

        return

    try:

        milestone = add_milestone(
            parts[0],
            parts[1],
            parts[2],
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    reminder_note = (
        "🔔 Dobby will remind CARE:\n"
        "• 1 month before\n"
    )

    if milestone.milestone_date is not None:

        reminder_note += (
            "• 2 weeks before\n"
            "• At the start of the milestone month"
        )

    else:

        reminder_note += (
            "• At the start of the milestone month\n\n"
            "ℹ️ Add the exact date later to enable "
            "the 2-week reminder."
        )

    await message.reply_text(
        "✅ MILESTONE ADDED\n\n"
        f"{format_milestone(milestone)}\n\n"
        f"{reminder_note}",
        reply_markup=build_milestone_keyboard(
            milestone.id
        ),
    )


# =========================================================
# UPDATE MILESTONE DATE
# =========================================================

async def update_milestone_date_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Update a milestone's date."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    raw_text = " ".join(
        context.args
    ).strip()

    parts = [
        part.strip()
        for part in raw_text.split(
            "|"
        )
    ]

    if len(parts) != 2:

        await message.reply_text(
            "Usage:\n"
            "/updatemilestonedate ID | DD-MM-YYYY\n\n"
            "Example:\n"
            "/updatemilestonedate 3 | 18-05-2027"
        )

        return

    try:

        milestone_id = int(
            parts[0]
        )

        milestone = update_milestone_date(
            milestone_id,
            parts[1],
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        "✅ MILESTONE DATE UPDATED\n\n"
        f"{format_milestone(milestone)}\n\n"
        "🔔 Reminder dates have been recalculated.",
        reply_markup=build_milestone_keyboard(
            milestone.id
        ),
    )


# =========================================================
# VIEW ONE MILESTONE
# =========================================================

async def milestone_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show one milestone."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "Usage:\n"
            "/milestone ID\n\n"
            "Example:\n"
            "/milestone 3"
        )

        return

    try:

        milestone_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid milestone ID."
        )

        return

    milestone = get_milestone(
        milestone_id
    )

    if milestone is None:

        await message.reply_text(
            "❌ Milestone not found."
        )

        return

    await message.reply_text(
        format_milestone(
            milestone
        ),
        reply_markup=build_milestone_keyboard(
            milestone_id
        ),
    )


# =========================================================
# ACTIVE MILESTONES
# =========================================================

async def active_milestones_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show all unfinished milestones."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        format_active_milestones()
    )


# =========================================================
# YEAR TRACKER
# =========================================================

async def milestone_year_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show all milestones for a year."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "Usage:\n"
            "/milestoneyear YEAR\n\n"
            "Example:\n"
            "/milestoneyear 2027"
        )

        return

    try:

        year = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid year."
        )

        return

    await message.reply_text(
        format_year_milestones(
            year
        )
    )


# =========================================================
# MONTH TRACKER
# =========================================================

async def milestone_month_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show all milestones for one month."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "Usage:\n"
            "/milestonemonth MM-YYYY\n\n"
            "Example:\n"
            "/milestonemonth 05-2027"
        )

        return

    try:

        month_text, year_text = (
            context.args[0].split(
                "-",
                maxsplit=1,
            )
        )

        month = int(
            month_text
        )

        year = int(
            year_text
        )

        if month < 1 or month > 12:
            raise ValueError

    except ValueError:

        await message.reply_text(
            "❌ Invalid month."
        )

        return

    await message.reply_text(
        format_month_milestones(
            year,
            month,
        )
    )


# =========================================================
# COMPLETED HISTORY
# =========================================================

async def milestone_history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show completed milestones for a year."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "Usage:\n"
            "/milestonehistory YEAR\n\n"
            "Example:\n"
            "/milestonehistory 2027"
        )

        return

    try:

        year = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid year."
        )

        return

    await message.reply_text(
        format_milestone_history(
            year
        )
    )


# =========================================================
# CANCEL MILESTONE
# =========================================================

async def cancel_milestone_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Cancel a milestone."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 2:

        await message.reply_text(
            "Usage:\n"
            "/cancelmilestone ID confirm\n\n"
            "Example:\n"
            "/cancelmilestone 3 confirm"
        )

        return

    try:

        milestone_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid milestone ID."
        )

        return

    if (
        context.args[1].lower()
        != "confirm"
    ):

        await message.reply_text(
            "❌ Please include 'confirm'."
        )

        return

    success = cancel_milestone(
        milestone_id
    )

    if not success:

        await message.reply_text(
            "❌ Milestone not found."
        )

        return

    await message.reply_text(
        f"✅ Milestone #{milestone_id} cancelled."
    )


# =========================================================
# ANNUAL PLAN
# =========================================================

async def milestone_annual_plan_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open yearly Milestone planning."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "Usage:\n"
            "/milestoneplan YEAR\n\n"
            "Example:\n"
            "/milestoneplan 2027"
        )

        return

    try:

        target_year = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid year."
        )

        return

    await message.reply_text(
        format_milestone_annual_plan(
            target_year
        ),
        reply_markup=build_annual_plan_keyboard(
            target_year
        ),
    )


# =========================================================
# SET ANNUAL MILESTONE GIFT
# =========================================================

async def set_milestone_gift_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Set yearly gift for a milestone category."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    raw_text = " ".join(
        context.args
    ).strip()

    parts = [
        part.strip()
        for part in raw_text.split(
            "|"
        )
    ]

    if len(parts) != 3:

        await message.reply_text(
            "Usage:\n"
            "/setmilestonegift YEAR | TYPE | GIFT\n\n"
            "Example:\n"
            "/setmilestonegift 2027 | baptism | "
            "Personalised Bible"
        )

        return

    try:

        target_year = int(
            parts[0]
        )

        set_milestone_gift(
            target_year,
            parts[1],
            parts[2],
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        "✅ MILESTONE GIFT UPDATED\n\n"
        + format_milestone_annual_plan(
            target_year
        ),
        reply_markup=build_annual_plan_keyboard(
            target_year
        ),
    )


# =========================================================
# MANUAL LIVE CHECK
# =========================================================

async def run_milestone_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Run today's Milestone scheduler manually."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    count = await send_due_milestone_reminders(
        context
    )

    await message.reply_text(
        "🏆 CARE Milestone reminder check complete.\n\n"
        f"{count} reminder(s) sent."
    )


# =========================================================
# TEST REMINDERS
# =========================================================

async def test_milestone_reminder_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Force-send a Milestone reminder for testing."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) < 2:

        await message.reply_text(
            "Examples:\n\n"
            "/testcaremilestonereminder lookout 2027\n"
            "/testcaremilestonereminder followup 2027\n"
            "/testcaremilestonereminder yearstart 2027\n"
            "/testcaremilestonereminder monthly 05-2027\n"
            "/testcaremilestonereminder month 3\n"
            "/testcaremilestonereminder twoweek 3"
        )

        return

    reminder_type = (
        context.args[0]
        .strip()
        .lower()
    )

    value = (
        context.args[1]
        .strip()
    )

    # -----------------------------------------------------
    # ANNUAL REMINDERS
    # -----------------------------------------------------

    if reminder_type in {
        "lookout",
        "followup",
        "yearstart",
    }:

        try:

            year = int(
                value
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid year."
            )

            return

        if reminder_type == "lookout":

            text = build_annual_lookout_reminder(
                year,
                followup=False,
            )

        elif reminder_type == "followup":

            text = build_annual_lookout_reminder(
                year,
                followup=True,
            )

        else:

            text = (
                format_year_milestones(
                    year
                )
                + "\n\n"
                "👀 Continue looking out for new milestones "
                "throughout the year."
            )

    # -----------------------------------------------------
    # MONTHLY REMINDER
    # -----------------------------------------------------

    elif reminder_type == "monthly":

        try:

            month_text, year_text = (
                value.split(
                    "-",
                    maxsplit=1,
                )
            )

            month = int(
                month_text
            )

            year = int(
                year_text
            )

            if month < 1 or month > 12:
                raise ValueError

        except ValueError:

            await message.reply_text(
                "❌ Use MM-YYYY."
            )

            return

        text = format_month_milestones(
            year,
            month,
        )

    # -----------------------------------------------------
    # 1 MONTH / 2 WEEK INDIVIDUAL TEST
    # -----------------------------------------------------

    elif reminder_type in {
        "month",
        "twoweek",
    }:

        try:

            milestone_id = int(
                value
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid milestone ID."
            )

            return

        milestone = get_milestone(
            milestone_id
        )

        if milestone is None:

            await message.reply_text(
                "❌ Milestone not found."
            )

            return

        if reminder_type == "month":

            text = build_one_month_reminder(
                milestone
            )

        else:

            if milestone.milestone_date is None:

                await message.reply_text(
                    "❌ This milestone only has a month.\n\n"
                    "Add an exact date first using:\n"
                    "/updatemilestonedate ID | DD-MM-YYYY"
                )

                return

            text = build_two_week_reminder(
                milestone
            )

    else:

        await message.reply_text(
            "❌ Unknown reminder type."
        )

        return

    sent = await send_care_milestone_message(
        context,
        text,
    )

    if sent:

        await message.reply_text(
            "✅ Milestone test reminder sent."
        )

    else:

        await message.reply_text(
            "❌ Test reminder could not be sent."
        )


# =========================================================
# BUTTON CALLBACKS
# =========================================================

async def handle_milestone_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle CARE Milestone buttons."""

    query = update.callback_query
    user = update.effective_user

    if query is None:
        return

    await query.answer()

    user_id = (
        user.id
        if user
        else None
    )

    if not is_care_leader(
        user_id
    ):

        await query.edit_message_text(
            "⛔ You do not have permission "
            "to manage CARE Milestones."
        )

        return

    callback_data = (
        query.data
        or ""
    )

    # -----------------------------------------------------
    # TOGGLE MILESTONE GIFT / CARD CHECKLIST
    # -----------------------------------------------------

    if callback_data.startswith(
        "caremilestone:toggle:"
    ):

        parts = callback_data.split(
            ":"
        )

        milestone_id = int(
            parts[2]
        )

        item_key = parts[3]

        try:

            milestone = (
                toggle_milestone_checklist_item(
                    milestone_id,
                    item_key,
                )
            )

        except ValueError as error:

            await query.edit_message_text(
                f"❌ {error}"
            )

            return

        await query.edit_message_text(
            format_milestone(
                milestone
            ),
            reply_markup=build_milestone_keyboard(
                milestone_id
            ),
        )

        return

    # -----------------------------------------------------
    # TOGGLE ANNUAL LOOKOUT CHECKLIST
    # -----------------------------------------------------

    if callback_data.startswith(
        "caremilestone:lookout:"
    ):

        parts = callback_data.split(
            ":"
        )

        target_year = int(
            parts[2]
        )

        item_key = parts[3]

        try:

            toggle_milestone_lookout_item(
                target_year,
                item_key,
            )

        except ValueError as error:

            await query.edit_message_text(
                f"❌ {error}"
            )

            return

        await query.edit_message_text(
            format_milestone_annual_plan(
                target_year
            ),
            reply_markup=build_annual_plan_keyboard(
                target_year
            ),
        )

        return


# =========================================================
# REGISTER HANDLERS + SCHEDULER
# =========================================================

def register_care_milestone_handlers(
    application: Application,
) -> None:
    """Register complete CARE Milestone system."""

    application.add_handler(
        CommandHandler(
            "addmilestone",
            add_milestone_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "updatemilestonedate",
            update_milestone_date_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "milestone",
            milestone_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "activemilestones",
            active_milestones_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "milestoneyear",
            milestone_year_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "milestonemonth",
            milestone_month_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "milestonehistory",
            milestone_history_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "cancelmilestone",
            cancel_milestone_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "milestoneplan",
            milestone_annual_plan_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "setmilestonegift",
            set_milestone_gift_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runcaremilestonecheck",
            run_milestone_check_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "testcaremilestonereminder",
            test_milestone_reminder_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_milestone_callback,
            pattern=r"^caremilestone:",
        )
    )

    # -----------------------------------------------------
    # LIVE SCHEDULER
    # -----------------------------------------------------

    if not CARE_MILESTONE_SCHEDULER_ENABLED:

        logger.info(
            "CARE Milestone scheduler is disabled."
        )

        return

    if application.job_queue is None:

        logger.error(
            "JobQueue unavailable. "
            "CARE Milestone scheduler not started."
        )

        return

    application.job_queue.run_daily(
        scheduled_milestone_job,
        time=time(
            hour=10,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        name="care_milestone_daily_check",
    )

    logger.info(
        "CARE Milestone scheduler enabled: "
        "daily at 10:00 AM Singapore time."
    )