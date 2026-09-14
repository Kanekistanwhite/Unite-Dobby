import logging
from datetime import (
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
    CARE_ENCOURAGEMENT_CHAT_ID,
    CARE_ENCOURAGEMENT_SCHEDULER_ENABLED,
    CARE_ENCOURAGEMENT_TOPIC_ID,
    CARE_LEADER_USER_IDS,
)
from services.care_encouragement_service import (
    ENCOURAGEMENT_ANNUAL_CHECKLIST,
    ENCOURAGEMENT_BATCH_CHECKLIST,
    add_encouragement_batch,
    add_encouragement_recipient,
    annual_encouragement_flag_is_set,
    build_encouragement_annual_reminder,
    build_encouragement_packing_reminder,
    build_monthly_encouragement_lookahead,
    cancel_encouragement_batch,
    encouragement_reminder_was_sent,
    format_active_encouragement_batches,
    format_batch_recipients,
    format_encouragement_annual_plan,
    format_encouragement_batch,
    format_encouragement_month,
    format_encouragement_recipient,
    get_active_encouragement_batches,
    get_current_encouragement_plan_year,
    get_encouragement_batch,
    get_encouragement_recipient,
    get_next_month,
    get_or_create_encouragement_annual_plan,
    get_singapore_today,
    mark_annual_encouragement_flag,
    record_encouragement_reminder_sent,
    remove_encouragement_recipient,
    set_encouragement_packing_date,
    toggle_encouragement_annual_item,
    toggle_encouragement_batch_item,
    toggle_recipient_item,
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
# BATCH KEYBOARD
# =========================================================

def build_encouragement_batch_keyboard(
    batch_id: int,
) -> InlineKeyboardMarkup:
    """Build batch checklist."""

    batch = get_encouragement_batch(
        batch_id
    )

    if batch is None:

        return InlineKeyboardMarkup(
            []
        )

    labels = {
        "recipients": "👥 Recipient List Confirmed",
        "cardsready": "💌 Cards Ready",
        "packsready": "🎁 Packs Ready",
        "packingdate": "📦 Packing Date Confirmed",
        "packed": "📦 Packs Packed",
        "cardscompleted": "✍️ Cards Completed",
        "distributed": "✅ Distribution Completed",
    }

    keyboard = []

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in ENCOURAGEMENT_BATCH_CHECKLIST.items():

        done = getattr(
            batch,
            field_name,
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    (
                        f"{'✅' if done else '⬜'} "
                        f"{labels[item_key]}"
                    ),
                    callback_data=(
                        "careencouragement:batchtoggle:"
                        f"{batch_id}:{item_key}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# RECIPIENT KEYBOARD
# =========================================================

def build_encouragement_recipient_keyboard(
    recipient_id: int,
) -> InlineKeyboardMarkup:
    """Build per-person distribution checklist."""

    recipient = get_encouragement_recipient(
        recipient_id
    )

    if recipient is None:

        return InlineKeyboardMarkup(
            []
        )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    (
                        f"{'✅' if recipient.card_given else '⬜'} "
                        "💌 Card Given"
                    ),
                    callback_data=(
                        "careencouragement:recipienttoggle:"
                        f"{recipient_id}:card"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    (
                        f"{'✅' if recipient.pack_given else '⬜'} "
                        "🎁 Pack Given"
                    ),
                    callback_data=(
                        "careencouragement:recipienttoggle:"
                        f"{recipient_id}:pack"
                    ),
                )
            ],
        ]
    )


# =========================================================
# ANNUAL PLAN KEYBOARD
# =========================================================

def build_encouragement_annual_keyboard(
    target_year: int,
) -> InlineKeyboardMarkup:
    """Build annual planning checklist."""

    plan = get_or_create_encouragement_annual_plan(
        target_year
    )

    labels = {
        "leaders": "📣 Cell Leaders Contacted",
        "exams": "📚 Exam Periods Collected",
        "crucial": "🎯 Crucial Periods Collected",
        "entered": "📝 Periods Entered",
        "contents": "🎁 Pack Contents Decided",
        "quantity": "🔢 Quantity Estimated",
        "items": "🛒 Items Purchased",
        "packaging": "📦 Packaging Purchased",
        "cards": "💌 Cards Ready",
        "stock": "✅ Initial Stock Prepared",
    }

    keyboard = []

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in ENCOURAGEMENT_ANNUAL_CHECKLIST.items():

        done = getattr(
            plan,
            field_name,
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    (
                        f"{'✅' if done else '⬜'} "
                        f"{labels[item_key]}"
                    ),
                    callback_data=(
                        "careencouragement:annualtoggle:"
                        f"{target_year}:{item_key}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# SEND MESSAGE
# =========================================================

async def send_care_encouragement_message(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> bool:
    """Send to CARE Encouragement topic."""

    if CARE_ENCOURAGEMENT_CHAT_ID is None:

        logger.error(
            "CARE_ENCOURAGEMENT_CHAT_ID is not configured."
        )

        return False

    kwargs = {}

    if CARE_ENCOURAGEMENT_TOPIC_ID is not None:

        kwargs[
            "message_thread_id"
        ] = CARE_ENCOURAGEMENT_TOPIC_ID

    try:

        await context.bot.send_message(
            chat_id=CARE_ENCOURAGEMENT_CHAT_ID,
            text=text,
            **kwargs,
        )

        return True

    except Exception:

        logger.exception(
            "CARE Encouragement reminder could not be sent."
        )

        return False


# =========================================================
# AUTOMATIC SCHEDULER
# =========================================================

async def send_due_encouragement_reminders(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Send all Encouragement reminders due today."""

    today = get_singapore_today()

    sent_count = 0

    # -----------------------------------------------------
    # 1 NOVEMBER — NEXT YEAR PLANNING
    # -----------------------------------------------------

    if (
        today.month == 11
        and today.day == 1
    ):

        target_year = (
            today.year + 1
        )

        if not annual_encouragement_flag_is_set(
            target_year,
            "lookout_open_sent",
        ):

            sent = await send_care_encouragement_message(
                context,
                build_encouragement_annual_reminder(
                    target_year,
                    followup=False,
                ),
            )

            if sent:

                mark_annual_encouragement_flag(
                    target_year,
                    "lookout_open_sent",
                )

                sent_count += 1

    # -----------------------------------------------------
    # 15 NOVEMBER — ANNUAL FOLLOW-UP
    # -----------------------------------------------------

    if (
        today.month == 11
        and today.day == 15
    ):

        target_year = (
            today.year + 1
        )

        if not annual_encouragement_flag_is_set(
            target_year,
            "lookout_followup_sent",
        ):

            sent = await send_care_encouragement_message(
                context,
                build_encouragement_annual_reminder(
                    target_year,
                    followup=True,
                ),
            )

            if sent:

                mark_annual_encouragement_flag(
                    target_year,
                    "lookout_followup_sent",
                )

                sent_count += 1

    # -----------------------------------------------------
    # 1ST OF EVERY MONTH
    # LOOK AHEAD TO NEXT MONTH
    # -----------------------------------------------------

    if today.day == 1:

        target_year, target_month = (
            get_next_month(
                today.year,
                today.month,
            )
        )

        reminder_type = (
            "monthly_lookahead"
        )

        if not encouragement_reminder_was_sent(
            target_year,
            target_month,
            reminder_type,
        ):

            text = (
                build_monthly_encouragement_lookahead(
                    target_year,
                    target_month,
                )
            )

            sent = await send_care_encouragement_message(
                context,
                text,
            )

            if sent:

                record_encouragement_reminder_sent(
                    target_year,
                    target_month,
                    reminder_type,
                )

                sent_count += 1

    # -----------------------------------------------------
    # PACKING SESSION REMINDERS
    # -----------------------------------------------------

    for batch in get_active_encouragement_batches():

        if batch.packing_date is None:
            continue

        if today >= batch.packing_date:
            continue

        one_week_due = (
            batch.packing_date
            - timedelta(
                days=7
            )
        )

        one_day_due = (
            batch.packing_date
            - timedelta(
                days=1
            )
        )

        one_week_type = (
            f"packing_7d:{batch.id}"
        )

        one_day_type = (
            f"packing_1d:{batch.id}"
        )

        one_day_sent = (
            encouragement_reminder_was_sent(
                batch.packing_date.year,
                batch.packing_date.month,
                one_day_type,
            )
        )

        # ---------------------------------------------
        # 1 DAY BEFORE
        # ---------------------------------------------

        if (
            today >= one_day_due
            and not one_day_sent
        ):

            sent = await send_care_encouragement_message(
                context,
                build_encouragement_packing_reminder(
                    batch,
                    one_day=True,
                ),
            )

            if sent:

                record_encouragement_reminder_sent(
                    batch.packing_date.year,
                    batch.packing_date.month,
                    one_day_type,
                )

                sent_count += 1

            continue

        # ---------------------------------------------
        # 1 WEEK BEFORE
        # ---------------------------------------------

        one_week_sent = (
            encouragement_reminder_was_sent(
                batch.packing_date.year,
                batch.packing_date.month,
                one_week_type,
            )
        )

        if (
            today >= one_week_due
            and today < one_day_due
            and not one_week_sent
        ):

            sent = await send_care_encouragement_message(
                context,
                build_encouragement_packing_reminder(
                    batch,
                    one_day=False,
                ),
            )

            if sent:

                record_encouragement_reminder_sent(
                    batch.packing_date.year,
                    batch.packing_date.month,
                    one_week_type,
                )

                sent_count += 1

    return sent_count


async def scheduled_encouragement_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Daily Encouragement scheduler."""

    logger.info(
        "Running CARE Encouragement reminder check."
    )

    count = await send_due_encouragement_reminders(
        context
    )

    logger.info(
        "CARE Encouragement check complete. "
        "%s reminder(s) sent.",
        count,
    )


# =========================================================
# ADD BATCH
# =========================================================

async def add_encouragement_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Create encouragement batch."""

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
            "/addencouragement TITLE | PERIOD\n\n"
            "Examples:\n"
            "/addencouragement Mid-Year Exams | 06-2027\n\n"
            "/addencouragement O Level Exams | "
            "20-10-2027 to 10-11-2027"
        )

        return

    try:

        batch = add_encouragement_batch(
            parts[0],
            parts[1],
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        "✅ ENCOURAGEMENT BATCH ADDED\n\n"
        f"{format_encouragement_batch(batch)}\n\n"
        "Next:\n"
        f"/addencouragementrecipient "
        f"{batch.id} | NAME",
        reply_markup=(
            build_encouragement_batch_keyboard(
                batch.id
            )
        ),
    )


# =========================================================
# VIEW BATCH
# =========================================================

async def encouragement_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show batch."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if (
        message is None
        or len(context.args) != 1
    ):

        if message is not None:

            await message.reply_text(
                "Usage:\n"
                "/encouragement BATCH_ID"
            )

        return

    try:

        batch_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid batch ID."
        )

        return

    batch = get_encouragement_batch(
        batch_id
    )

    if batch is None:

        await message.reply_text(
            "❌ Encouragement batch not found."
        )

        return

    await message.reply_text(
        format_encouragement_batch(
            batch
        ),
        reply_markup=(
            build_encouragement_batch_keyboard(
                batch_id
            )
        ),
    )


# =========================================================
# ADD RECIPIENT
# =========================================================

async def add_encouragement_recipient_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add recipient."""

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
            "/addencouragementrecipient "
            "BATCH_ID | NAME"
        )

        return

    try:

        batch_id = int(
            parts[0]
        )

        recipient = add_encouragement_recipient(
            batch_id,
            parts[1],
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        "✅ RECIPIENT ADDED\n\n"
        f"{format_encouragement_recipient(recipient)}",
        reply_markup=(
            build_encouragement_recipient_keyboard(
                recipient.id
            )
        ),
    )


# =========================================================
# RECIPIENT LIST
# =========================================================

async def encouragement_recipients_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if (
        message is None
        or len(context.args) != 1
    ):

        if message is not None:

            await message.reply_text(
                "Usage:\n"
                "/encouragementrecipients BATCH_ID"
            )

        return

    try:

        batch_id = int(
            context.args[0]
        )

        text = format_batch_recipients(
            batch_id
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        text
    )


# =========================================================
# ONE RECIPIENT
# =========================================================

async def encouragement_recipient_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if (
        message is None
        or len(context.args) != 1
    ):

        if message is not None:

            await message.reply_text(
                "Usage:\n"
                "/encouragementrecipient RECIPIENT_ID"
            )

        return

    try:

        recipient_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid recipient ID."
        )

        return

    recipient = get_encouragement_recipient(
        recipient_id
    )

    if recipient is None:

        await message.reply_text(
            "❌ Recipient not found."
        )

        return

    await message.reply_text(
        format_encouragement_recipient(
            recipient
        ),
        reply_markup=(
            build_encouragement_recipient_keyboard(
                recipient_id
            )
        ),
    )


# =========================================================
# REMOVE RECIPIENT
# =========================================================

async def remove_encouragement_recipient_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if (
        message is None
        or len(context.args) != 2
    ):

        if message is not None:

            await message.reply_text(
                "Usage:\n"
                "/removeencouragementrecipient "
                "RECIPIENT_ID confirm"
            )

        return

    try:

        recipient_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid recipient ID."
        )

        return

    if context.args[1].lower() != "confirm":

        await message.reply_text(
            "❌ Please include 'confirm'."
        )

        return

    removed, name = (
        remove_encouragement_recipient(
            recipient_id
        )
    )

    if not removed:

        await message.reply_text(
            "❌ Recipient not found."
        )

        return

    await message.reply_text(
        "✅ RECIPIENT REMOVED\n\n"
        f"👤 {name}"
    )


# =========================================================
# PACKING DATE
# =========================================================

async def set_encouragement_packing_date_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

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
            "/setencouragementpacking "
            "BATCH_ID | DD-MM-YYYY"
        )

        return

    try:

        batch_id = int(
            parts[0]
        )

        batch = set_encouragement_packing_date(
            batch_id,
            parts[1],
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        "✅ PACKING DATE SET\n\n"
        f"{format_encouragement_batch(batch)}\n\n"
        "🔔 Dobby will remind CARE:\n"
        "• 1 week before packing\n"
        "• 1 day before packing",
        reply_markup=(
            build_encouragement_batch_keyboard(
                batch.id
            )
        ),
    )


# =========================================================
# ACTIVE / MONTH
# =========================================================

async def active_encouragement_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    await update.effective_message.reply_text(
        format_active_encouragement_batches()
    )


async def encouragement_month_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if (
        message is None
        or len(context.args) != 1
    ):

        if message is not None:

            await message.reply_text(
                "Usage:\n"
                "/encouragementmonth MM-YYYY"
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
        format_encouragement_month(
            year,
            month,
        )
    )


# =========================================================
# CANCEL
# =========================================================

async def cancel_encouragement_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if (
        message is None
        or len(context.args) != 2
    ):

        if message is not None:

            await message.reply_text(
                "Usage:\n"
                "/cancelencouragement "
                "BATCH_ID confirm"
            )

        return

    try:

        batch_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid batch ID."
        )

        return

    if context.args[1].lower() != "confirm":

        await message.reply_text(
            "❌ Please include 'confirm'."
        )

        return

    success = cancel_encouragement_batch(
        batch_id
    )

    if not success:

        await message.reply_text(
            "❌ Encouragement batch not found."
        )

        return

    await message.reply_text(
        f"✅ Encouragement batch #{batch_id} cancelled."
    )


# =========================================================
# ANNUAL PLAN
# =========================================================

async def encouragement_plan_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open annual Encouragement preparation."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if context.args:

        try:

            target_year = int(
                context.args[0]
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid year."
            )

            return

    else:

        target_year = (
            get_current_encouragement_plan_year()
        )

    await message.reply_text(
        format_encouragement_annual_plan(
            target_year
        ),
        reply_markup=(
            build_encouragement_annual_keyboard(
                target_year
            )
        ),
    )


# =========================================================
# MANUAL CHECK
# =========================================================

async def run_encouragement_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    count = (
        await send_due_encouragement_reminders(
            context
        )
    )

    await update.effective_message.reply_text(
        "💌 CARE Encouragement reminder check complete.\n\n"
        f"{count} reminder(s) sent."
    )


# =========================================================
# TEST REMINDERS
# =========================================================

async def test_encouragement_reminder_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Force-send reminder for testing."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if (
        message is None
        or len(context.args) != 2
    ):

        if message is not None:

            await message.reply_text(
                "Examples:\n\n"
                "/testcareencouragementreminder "
                "annual 2027\n\n"
                "/testcareencouragementreminder "
                "followup 2027\n\n"
                "/testcareencouragementreminder "
                "monthly 06-2027\n\n"
                "/testcareencouragementreminder "
                "packingweek 1\n\n"
                "/testcareencouragementreminder "
                "packingday 1"
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

    if reminder_type in {
        "annual",
        "followup",
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

        text = (
            build_encouragement_annual_reminder(
                year,
                followup=(
                    reminder_type == "followup"
                ),
            )
        )

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

        text = (
            build_monthly_encouragement_lookahead(
                year,
                month,
            )
        )

    elif reminder_type in {
        "packingweek",
        "packingday",
    }:

        try:

            batch_id = int(
                value
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid batch ID."
            )

            return

        batch = get_encouragement_batch(
            batch_id
        )

        if batch is None:

            await message.reply_text(
                "❌ Encouragement batch not found."
            )

            return

        if batch.packing_date is None:

            await message.reply_text(
                "❌ Set a packing date first."
            )

            return

        text = (
            build_encouragement_packing_reminder(
                batch,
                one_day=(
                    reminder_type == "packingday"
                ),
            )
        )

    else:

        await message.reply_text(
            "❌ Unknown reminder type."
        )

        return

    sent = await send_care_encouragement_message(
        context,
        text,
    )

    if sent:

        await message.reply_text(
            "✅ Encouragement test reminder sent."
        )

    else:

        await message.reply_text(
            "❌ Test reminder could not be sent."
        )


# =========================================================
# CALLBACKS
# =========================================================

async def handle_encouragement_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle Encouragement buttons."""

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
            "to manage CARE Encouragement."
        )

        return

    callback_data = (
        query.data
        or ""
    )

    if callback_data.startswith(
        "careencouragement:batchtoggle:"
    ):

        parts = callback_data.split(
            ":"
        )

        batch_id = int(
            parts[2]
        )

        item_key = parts[3]

        try:

            batch = toggle_encouragement_batch_item(
                batch_id,
                item_key,
            )

        except ValueError as error:

            await query.edit_message_text(
                f"❌ {error}"
            )

            return

        await query.edit_message_text(
            format_encouragement_batch(
                batch
            ),
            reply_markup=(
                build_encouragement_batch_keyboard(
                    batch_id
                )
            ),
        )

        return

    if callback_data.startswith(
        "careencouragement:recipienttoggle:"
    ):

        parts = callback_data.split(
            ":"
        )

        recipient_id = int(
            parts[2]
        )

        item_key = parts[3]

        try:

            recipient = toggle_recipient_item(
                recipient_id,
                item_key,
            )

        except ValueError as error:

            await query.edit_message_text(
                f"❌ {error}"
            )

            return

        await query.edit_message_text(
            format_encouragement_recipient(
                recipient
            ),
            reply_markup=(
                build_encouragement_recipient_keyboard(
                    recipient_id
                )
            ),
        )

        return

    if callback_data.startswith(
        "careencouragement:annualtoggle:"
    ):

        parts = callback_data.split(
            ":"
        )

        target_year = int(
            parts[2]
        )

        item_key = parts[3]

        try:

            toggle_encouragement_annual_item(
                target_year,
                item_key,
            )

        except ValueError as error:

            await query.edit_message_text(
                f"❌ {error}"
            )

            return

        await query.edit_message_text(
            format_encouragement_annual_plan(
                target_year
            ),
            reply_markup=(
                build_encouragement_annual_keyboard(
                    target_year
                )
            ),
        )

        return


# =========================================================
# REGISTER
# =========================================================

def register_care_encouragement_handlers(
    application: Application,
) -> None:
    """Register complete CARE Encouragement system."""

    application.add_handler(
        CommandHandler(
            "addencouragement",
            add_encouragement_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "encouragement",
            encouragement_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "addencouragementrecipient",
            add_encouragement_recipient_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "encouragementrecipients",
            encouragement_recipients_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "encouragementrecipient",
            encouragement_recipient_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "removeencouragementrecipient",
            remove_encouragement_recipient_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "setencouragementpacking",
            set_encouragement_packing_date_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "activeencouragement",
            active_encouragement_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "encouragementmonth",
            encouragement_month_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "cancelencouragement",
            cancel_encouragement_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "encouragementplan",
            encouragement_plan_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runcareencouragementcheck",
            run_encouragement_check_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "testcareencouragementreminder",
            test_encouragement_reminder_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_encouragement_callback,
            pattern=r"^careencouragement:",
        )
    )

    # -----------------------------------------------------
    # LIVE SCHEDULER
    # -----------------------------------------------------

    if not CARE_ENCOURAGEMENT_SCHEDULER_ENABLED:

        logger.info(
            "CARE Encouragement scheduler is disabled."
        )

        return

    if application.job_queue is None:

        logger.error(
            "JobQueue unavailable. "
            "CARE Encouragement scheduler not started."
        )

        return

    application.job_queue.run_daily(
        scheduled_encouragement_job,
        time=time(
            hour=10,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        name="care_encouragement_daily_check",
    )

    logger.info(
        "CARE Encouragement scheduler enabled: "
        "daily at 10:00 AM Singapore time."
    )