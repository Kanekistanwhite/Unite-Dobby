import logging
from calendar import month_name
from datetime import (
    datetime,
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
    CARE_BIRTHDAY_CHAT_ID,
    CARE_BIRTHDAY_SCHEDULER_ENABLED,
    CARE_BIRTHDAY_TOPIC_ID,
    CARE_LEADER_USER_IDS,
)
from services.care_birthday_service import (
    CARE_ANNUAL_GIFT_CHECKLIST,
    CARE_BIRTHDAY_ALL_CHECKLIST,
    CARE_BIRTHDAY_PREP_CHECKLIST,
    annual_reminder_was_sent,
    build_annual_prep_reminder_text,
    format_care_annual_prep,
    format_care_birthday_batch,
    format_care_birthday_month,
    format_care_birthday_roster,
    format_celebrant_list,
    add_care_birthday_member,
    deactivate_care_birthday_member,
    get_care_birthday_member_by_id,
    get_care_birthday_member_by_name,
    get_current_annual_prep_year,
    get_current_care_birthday_period,
    get_first_sunday,
    get_incomplete_preparation_items,
    get_next_month,
    get_or_create_care_annual_prep,
    get_or_create_care_birthday_batch,
    get_singapore_now,
    has_care_birthday_reminder_been_sent,
    mark_annual_reminder_sent,
    record_care_birthday_reminder_sent,
    seed_care_birthday_roster,
    toggle_care_annual_prep_item,
    toggle_care_birthday_checklist_item,
)


logger = logging.getLogger(
    __name__
)

SINGAPORE_TIMEZONE = ZoneInfo(
    "Asia/Singapore"
)


# =========================================================
# PERMISSIONS
# =========================================================

def is_care_leader(
    user_id: int | None,
) -> bool:
    """Check whether user may manage CARE."""

    if user_id is None:
        return False

    return user_id in CARE_LEADER_USER_IDS


async def check_care_permission(
    update: Update,
) -> bool:
    """Allow only approved CARE leaders."""

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
# MONTHLY BIRTHDAY BUTTONS
# =========================================================

def build_batch_view_keyboard(
    year: int,
    month: int,
) -> InlineKeyboardMarkup:
    """Buttons underneath birthday batch summary."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Update Checklist",
                    callback_data=(
                        f"carebirthday:checklist:"
                        f"{year}:{month}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 Annual Gift Prep",
                    callback_data=(
                        "carebirthday:annual:"
                        f"{get_current_annual_prep_year()}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Birthdays",
                    callback_data="panel:care:birthdays",
                )
            ],
        ]
    )


def build_checklist_keyboard(
    year: int,
    month: int,
) -> InlineKeyboardMarkup:
    """Interactive monthly CARE Birthday checklist."""

    batch = get_or_create_care_birthday_batch(
        year,
        month,
    )

    keyboard = []

    button_labels = {
        "celebrants": "👥 Celebrants Confirmed",
        "idea": "💡 Celebration Idea",
        "cake": "🎂 Cake Arranged",
        "gifts": "🎁 Gift Packs Ready",
        "cards": "💌 Cards Ready",
        "announcement": "📣 Announcement Sent",
        "celebration": "🥳 Celebration Completed",
        "distribution": "📦 Distribution Completed",
    }

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in CARE_BIRTHDAY_ALL_CHECKLIST.items():

        completed = getattr(
            batch,
            field_name,
        )

        icon = (
            "✅"
            if completed
            else "⬜"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{icon} {button_labels[item_key]}",
                    callback_data=(
                        f"carebirthday:toggle:"
                        f"{year}:{month}:{item_key}"
                    ),
                )
            ]
        )

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "📋 View Batch",
                    callback_data=(
                        f"carebirthday:view:"
                        f"{year}:{month}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 Annual Gift Prep",
                    callback_data=(
                        "carebirthday:annual:"
                        f"{get_current_annual_prep_year()}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Birthdays",
                    callback_data="panel:care:birthdays",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# ANNUAL GIFT PREP BUTTONS
# =========================================================

def build_annual_prep_keyboard(
    target_year: int,
) -> InlineKeyboardMarkup:
    """Interactive Annual Gift Prep checklist."""

    annual = get_or_create_care_annual_prep(
        target_year
    )

    keyboard = []

    button_labels = {
        "gift": "🎁 Gift Finalised",
        "quantity": "🔢 Quantity Confirmed",
        "purchase_gifts": "🛒 Gifts Purchased",
        "materials": "📦 Packing Materials Purchased",
        "arrived": "📥 All Items Received",
        "packed": "🎀 Gifts Packed",
        "counted": "🔢 Gift Packs Counted",
        "stock": "✅ Sufficient Stock Confirmed",
    }

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in CARE_ANNUAL_GIFT_CHECKLIST.items():

        completed = getattr(
            annual,
            field_name,
        )

        icon = (
            "✅"
            if completed
            else "⬜"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{icon} {button_labels[item_key]}",
                    callback_data=(
                        "carebirthday:annualtoggle:"
                        f"{target_year}:{item_key}"
                    ),
                )
            ]
        )

    year, month = (
        get_current_care_birthday_period()
    )

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "🎂 Monthly Birthday Batch",
                    callback_data=(
                        f"carebirthday:view:"
                        f"{year}:{month}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Birthdays",
                    callback_data="panel:care:birthdays",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# PARSING
# =========================================================

def parse_month_year(
    value: str,
) -> tuple[int, int]:
    """Convert MM-YYYY into year/month."""

    month_text, year_text = value.split(
        "-",
        maxsplit=1,
    )

    month = int(
        month_text
    )

    year = int(
        year_text
    )

    datetime(
        year,
        month,
        1,
    )

    return (
        year,
        month,
    )


def parse_day_month(
    value: str,
) -> tuple[int, int]:
    """Convert DD-MM into day/month."""

    day_text, month_text = value.split(
        "-",
        maxsplit=1,
    )

    day = int(
        day_text
    )

    month = int(
        month_text
    )

    # Leap year allows 29 February.
    datetime(
        2000,
        month,
        day,
    )

    return (
        day,
        month,
    )


# =========================================================
# MONTHLY REMINDER TEXT
# =========================================================

def build_open_reminder(
    year: int,
    month: int,
) -> str:
    """Build 2nd-of-month preparation reminder."""

    celebration = get_first_sunday(
        year,
        month,
    )

    return (
        f"🎂 {month_name[month].upper()} "
        "BIRTHDAY PREPARATION\n\n"
        f"{format_celebrant_list(month)}\n\n"
        "📋 Preparation Checklist:\n"
        "⬜ Celebrant list confirmed\n"
        "⬜ Celebration idea ready\n"
        "⬜ Cake arranged\n"
        "⬜ Gift packs ready\n"
        "⬜ Birthday cards ready\n\n"
        f"🥳 Celebration: "
        f"{celebration.strftime('%A')}, "
        f"{celebration.day} "
        f"{celebration.strftime('%B %Y')}\n\n"
        "Time to start preparing for next month's birthdays 🙌"
    )


def build_progress_reminder(
    year: int,
    month: int,
    final: bool = False,
) -> str | None:
    """Build 15th or 25th outstanding-item reminder."""

    batch = get_or_create_care_birthday_batch(
        year,
        month,
    )

    incomplete = get_incomplete_preparation_items(
        batch
    )

    if not incomplete:
        return None

    lines = []

    for item in incomplete:
        lines.append(
            f"⬜ {item}"
        )

    if final:
        heading = (
            f"⚠️ {month_name[month].upper()} "
            "BIRTHDAY FINAL PREPARATION CHECK"
        )

        ending = (
            "Please settle these before the new month begins."
        )

    else:
        heading = (
            f"🔔 {month_name[month].upper()} "
            "BIRTHDAY PROGRESS CHECK"
        )

        ending = (
            "These items are still outstanding."
        )

    return (
        f"{heading}\n\n"
        + "\n".join(lines)
        + f"\n\n{ending}"
    )


def build_announcement_reminder(
    year: int,
    month: int,
) -> str:
    """Build monthly birthday-announcement reminder."""

    return (
        f"📣 {month_name[month].upper()} "
        "BIRTHDAY ANNOUNCEMENT REMINDER\n\n"
        f"{format_celebrant_list(month)}\n\n"
        "Please send this month's birthday announcement "
        "into the Youth Ministry Telegram channel today.\n\n"
        "After sending it, mark:\n"
        "✅ Announcement Sent\n"
        "inside Dobby's CARE Birthday checklist."
    )


def build_distribution_reminder(
    year: int,
    month: int,
    weekly: bool = False,
) -> str:
    """Build post-celebration distribution reminder."""

    if weekly:
        heading = (
            f"🔔 {month_name[month].upper()} "
            "BIRTHDAY DISTRIBUTION FOLLOW-UP"
        )

    else:
        heading = (
            f"📦 {month_name[month].upper()} "
            "BIRTHDAY DISTRIBUTION CHECK"
        )

    return (
        f"{heading}\n\n"
        "Please check:\n\n"
        "□ Have all gift packs been given out?\n"
        "□ Have all birthday cards been given out?\n"
        "□ Was anyone absent?\n"
        "□ Is anyone still outstanding?\n\n"
        "Once everyone has received everything, "
        "mark:\n"
        "✅ Distribution Completed\n"
        "inside Dobby."
    )


# =========================================================
# SEND MESSAGE
# =========================================================

async def send_care_birthday_message(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> bool:
    """Send reminder to CARE Birthday destination."""

    if CARE_BIRTHDAY_CHAT_ID is None:
        logger.error(
            "CARE_BIRTHDAY_CHAT_ID is not configured."
        )

        return False

    kwargs = {}

    if CARE_BIRTHDAY_TOPIC_ID is not None:
        kwargs[
            "message_thread_id"
        ] = CARE_BIRTHDAY_TOPIC_ID

    try:
        await context.bot.send_message(
            chat_id=CARE_BIRTHDAY_CHAT_ID,
            text=text,
            **kwargs,
        )

        return True

    except Exception:
        logger.exception(
            "CARE Birthday reminder could not be sent."
        )

        return False


# =========================================================
# AUTOMATIC MONTHLY + ANNUAL REMINDERS
# =========================================================

async def send_due_care_birthday_reminders(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Send any CARE Birthday reminders due today."""

    now = get_singapore_now()
    today = now.date()

    sent_count = 0

    # =====================================================
    # MONTHLY: 1ST — ANNOUNCEMENT REMINDER
    # =====================================================

    if today.day == 1:

        year = today.year
        month = today.month

        batch = get_or_create_care_birthday_batch(
            year,
            month,
        )

        reminder_type = "announcement"

        if (
            not batch.monthly_announcement_sent
            and not has_care_birthday_reminder_been_sent(
                year,
                month,
                reminder_type,
            )
        ):

            sent = await send_care_birthday_message(
                context,
                build_announcement_reminder(
                    year,
                    month,
                ),
            )

            if sent:
                record_care_birthday_reminder_sent(
                    year,
                    month,
                    reminder_type,
                )

                sent_count += 1

    # =====================================================
    # MONTHLY: 2ND / 15TH / 25TH
    # =====================================================

    if today.day in {
        2,
        15,
        25,
    }:

        year, month = get_next_month(
            today.year,
            today.month,
        )

        get_or_create_care_birthday_batch(
            year,
            month,
        )

        if today.day == 2:

            reminder_type = "open"

            text = build_open_reminder(
                year,
                month,
            )

        elif today.day == 15:

            reminder_type = "midmonth"

            text = build_progress_reminder(
                year,
                month,
                final=False,
            )

        else:

            reminder_type = "final"

            text = build_progress_reminder(
                year,
                month,
                final=True,
            )

        if (
            text is not None
            and not has_care_birthday_reminder_been_sent(
                year,
                month,
                reminder_type,
            )
        ):

            sent = await send_care_birthday_message(
                context,
                text,
            )

            if sent:
                record_care_birthday_reminder_sent(
                    year,
                    month,
                    reminder_type,
                )

                sent_count += 1

    # =====================================================
    # MONTHLY: POST-CELEBRATION DISTRIBUTION
    # =====================================================

    year = today.year
    month = today.month

    batch = get_or_create_care_birthday_batch(
        year,
        month,
    )

    first_sunday = get_first_sunday(
        year,
        month,
    )

    first_followup = (
        first_sunday
        + timedelta(
            days=1
        )
    )

    if (
        today >= first_followup
        and not batch.distribution_completed
    ):

        days_after_first_followup = (
            today - first_followup
        ).days

        should_send = (
            days_after_first_followup == 0
            or (
                days_after_first_followup > 0
                and days_after_first_followup % 7 == 0
            )
        )

        if should_send:

            reminder_type = (
                "distribution_"
                + today.isoformat()
            )

            if not has_care_birthday_reminder_been_sent(
                year,
                month,
                reminder_type,
            ):

                text = build_distribution_reminder(
                    year,
                    month,
                    weekly=(
                        days_after_first_followup > 0
                    ),
                )

                sent = await send_care_birthday_message(
                    context,
                    text,
                )

                if sent:
                    record_care_birthday_reminder_sent(
                        year,
                        month,
                        reminder_type,
                    )

                    sent_count += 1

    # =====================================================
    # ANNUAL GIFT PREP
    # =====================================================

    annual_target_year = (
        today.year + 1
    )

    annual_heading = None
    annual_flag = None
    annual_full_checklist = False

    # 1 NOVEMBER — OPEN ANNUAL PREP
    if (
        today.month == 11
        and today.day == 1
    ):

        annual_heading = (
            f"🎁 {annual_target_year} "
            "ANNUAL BIRTHDAY GIFT PREP"
        )

        annual_flag = (
            "open_reminder_sent"
        )

        annual_full_checklist = True

    # 15 NOVEMBER — PROGRESS CHECK
    elif (
        today.month == 11
        and today.day == 15
    ):

        annual_heading = (
            f"🔔 {annual_target_year} "
            "ANNUAL GIFT PREP PROGRESS CHECK"
        )

        annual_flag = (
            "nov15_reminder_sent"
        )

    # 1 DECEMBER — PROGRESS CHECK
    elif (
        today.month == 12
        and today.day == 1
    ):

        annual_heading = (
            f"🔔 {annual_target_year} "
            "ANNUAL GIFT PREP — DECEMBER CHECK"
        )

        annual_flag = (
            "dec1_reminder_sent"
        )

    # 15 DECEMBER — FINAL PACKING CHECK
    elif (
        today.month == 12
        and today.day == 15
    ):

        annual_heading = (
            f"⚠️ {annual_target_year} "
            "ANNUAL GIFT PREP — FINAL PACKING CHECK"
        )

        annual_flag = (
            "dec15_reminder_sent"
        )

    # 25 DECEMBER — FINAL WARNING
    elif (
        today.month == 12
        and today.day == 25
    ):

        annual_heading = (
            f"🚨 {annual_target_year} "
            "ANNUAL GIFT PREP — FINAL REMINDER"
        )

        annual_flag = (
            "dec25_reminder_sent"
        )

    if (
        annual_heading is not None
        and annual_flag is not None
    ):

        already_sent = (
            annual_reminder_was_sent(
                annual_target_year,
                annual_flag,
            )
        )

        if not already_sent:

            annual_text = (
                build_annual_prep_reminder_text(
                    annual_target_year,
                    annual_heading,
                    full_checklist=annual_full_checklist,
                )
            )

            if annual_text is not None:

                sent = await send_care_birthday_message(
                    context,
                    annual_text,
                )

                if sent:

                    mark_annual_reminder_sent(
                        annual_target_year,
                        annual_flag,
                    )

                    sent_count += 1

    return sent_count


async def scheduled_care_birthday_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Automatic daily CARE Birthday check."""

    logger.info(
        "Running CARE Birthday reminder check."
    )

    sent_count = await send_due_care_birthday_reminders(
        context
    )

    logger.info(
        "CARE Birthday check complete. "
        "%s reminder(s) sent.",
        sent_count,
    )


# =========================================================
# ROSTER MANAGEMENT COMMANDS
# =========================================================

async def care_birthday_roster_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the complete active CARE Birthday roster."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        format_care_birthday_roster()
    )


async def add_care_birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add or reactivate one CARE Birthday member."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    raw = " ".join(
        context.args
    ).strip()

    if "|" not in raw:
        await message.reply_text(
            "Usage:\n"
            "/addcarebirthday NAME | DD-MM\n\n"
            "Example:\n"
            "/addcarebirthday John Tan | 14-03"
        )
        return

    name_text, birthday_text = [
        part.strip()
        for part in raw.split(
            "|",
            maxsplit=1,
        )
    ]

    if not name_text:
        await message.reply_text(
            "❌ Name cannot be empty."
        )
        return

    try:
        day, month = parse_day_month(
            birthday_text
        )

    except (
        ValueError,
        TypeError,
    ):
        await message.reply_text(
            "❌ Invalid birthday.\n\n"
            "Use DD-MM, for example:\n"
            "/addcarebirthday John Tan | 14-03"
        )
        return

    try:
        member, reactivated = add_care_birthday_member(
            name_text,
            day,
            month,
        )

    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    action = (
        "reactivated"
        if reactivated
        else "added"
    )

    await message.reply_text(
        "✅ CARE BIRTHDAY UPDATED\n\n"
        f"{member.display_name} was {action}.\n"
        f"Birthday: {member.birthday_day} "
        f"{month_name[member.birthday_month]}"
    )


async def remove_care_birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Start removal of one CARE Birthday member."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    name = " ".join(
        context.args
    ).strip()

    if not name:
        await message.reply_text(
            "Usage:\n"
            "/removecarebirthday NAME\n\n"
            "Example:\n"
            "/removecarebirthday John Tan"
        )
        return

    member = get_care_birthday_member_by_name(
        name
    )

    if (
        member is None
        or not member.is_active
    ):
        await message.reply_text(
            "❌ No active CARE Birthday member "
            "was found with that name."
        )
        return

    await message.reply_text(
        "🗑 REMOVE CARE BIRTHDAY\n\n"
        f"Name: {member.display_name}\n"
        f"Birthday: {member.birthday_day} "
        f"{month_name[member.birthday_month]}\n\n"
        "Remove this person from the active "
        "CARE Birthday roster?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Confirm Remove",
                        callback_data=(
                            "carebirthday:removeconfirm:"
                            f"{member.id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="carebirthday:removecancel",
                    ),
                ]
            ]
        ),
    )


# =========================================================
# MONTHLY COMMANDS
# =========================================================

async def setup_care_birthdays_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Load CARE Birthday roster."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    created, updated = (
        seed_care_birthday_roster()
    )

    await message.reply_text(
        "✅ CARE BIRTHDAY ROSTER UPDATED\n\n"
        f"New members: {created}\n"
        f"Existing members updated: {updated}"
    )


async def care_birthday_month_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show birthdays for selected month."""

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
            "/carebirthdaymonth MM-YYYY"
        )

        return

    try:
        year, month = parse_month_year(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid month."
        )

        return

    await message.reply_text(
        format_care_birthday_month(
            year,
            month,
        )
    )


async def care_birthday_batch_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show CARE Birthday batch."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if context.args:

        try:
            year, month = parse_month_year(
                context.args[0]
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid month."
            )

            return

    else:

        year, month = (
            get_current_care_birthday_period()
        )

    await message.reply_text(
        format_care_birthday_batch(
            year,
            month,
        ),
        reply_markup=build_batch_view_keyboard(
            year,
            month,
        ),
    )


async def care_birthday_checklist_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open monthly CARE Birthday checklist."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    year, month = (
        get_current_care_birthday_period()
    )

    await message.reply_text(
        format_care_birthday_batch(
            year,
            month,
        ),
        reply_markup=build_checklist_keyboard(
            year,
            month,
        ),
    )


# =========================================================
# ANNUAL GIFT PREP COMMAND
# =========================================================

async def care_annual_prep_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open Annual Gift Prep checklist."""

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

            if target_year < 2000:
                raise ValueError

        except ValueError:

            await message.reply_text(
                "❌ Invalid year.\n\n"
                "Example:\n"
                "/careannualprep 2027"
            )

            return

    else:

        target_year = (
            get_current_annual_prep_year()
        )

    await message.reply_text(
        format_care_annual_prep(
            target_year
        ),
        reply_markup=build_annual_prep_keyboard(
            target_year
        ),
    )


# =========================================================
# MANUAL REMINDER CHECK
# =========================================================

async def run_care_birthday_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Manually run today's automatic reminder check."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    sent_count = await send_due_care_birthday_reminders(
        context
    )

    await message.reply_text(
        "🔔 CARE Birthday reminder check complete.\n\n"
        f"{sent_count} reminder(s) sent."
    )


# =========================================================
# TEST MONTHLY REMINDER
# =========================================================

async def test_care_birthday_reminder_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Force-send a test monthly CARE Birthday reminder."""

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
            "/testcarebirthdayreminder TYPE MM-YYYY\n\n"
            "Types:\n"
            "open\n"
            "mid\n"
            "final\n"
            "announcement\n"
            "distribution\n\n"
            "Example:\n"
            "/testcarebirthdayreminder open 10-2026"
        )

        return

    reminder_type = (
        context.args[0]
        .strip()
        .lower()
    )

    try:
        year, month = parse_month_year(
            context.args[1]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid month."
        )

        return

    if reminder_type == "open":

        text = build_open_reminder(
            year,
            month,
        )

    elif reminder_type == "mid":

        text = build_progress_reminder(
            year,
            month,
            final=False,
        )

        if text is None:
            text = (
                "✅ All preparation items "
                "are already completed."
            )

    elif reminder_type == "final":

        text = build_progress_reminder(
            year,
            month,
            final=True,
        )

        if text is None:
            text = (
                "✅ All preparation items "
                "are already completed."
            )

    elif reminder_type == "announcement":

        text = build_announcement_reminder(
            year,
            month,
        )

    elif reminder_type == "distribution":

        text = build_distribution_reminder(
            year,
            month,
        )

    else:

        await message.reply_text(
            "❌ Unknown reminder type."
        )

        return

    sent = await send_care_birthday_message(
        context,
        text,
    )

    if sent:

        await message.reply_text(
            "✅ Test reminder sent to the "
            "CARE Birthday destination."
        )

    else:

        await message.reply_text(
            "❌ Test reminder could not be sent."
        )


# =========================================================
# TEST ANNUAL GIFT PREP REMINDER
# =========================================================

async def test_care_annual_reminder_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Force-send an Annual Gift Prep reminder."""

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
            "/testcareannualreminder TYPE YEAR\n\n"
            "Types:\n"
            "open\n"
            "nov15\n"
            "dec1\n"
            "dec15\n"
            "dec25\n\n"
            "Example:\n"
            "/testcareannualreminder open 2027"
        )

        return

    reminder_type = (
        context.args[0]
        .strip()
        .lower()
    )

    try:
        target_year = int(
            context.args[1]
        )

        if target_year < 2000:
            raise ValueError

    except ValueError:

        await message.reply_text(
            "❌ Invalid year."
        )

        return

    if reminder_type == "open":

        heading = (
            f"🎁 {target_year} "
            "ANNUAL BIRTHDAY GIFT PREP"
        )

        full_checklist = True

    elif reminder_type == "nov15":

        heading = (
            f"🔔 {target_year} "
            "ANNUAL GIFT PREP PROGRESS CHECK"
        )

        full_checklist = False

    elif reminder_type == "dec1":

        heading = (
            f"🔔 {target_year} "
            "ANNUAL GIFT PREP — DECEMBER CHECK"
        )

        full_checklist = False

    elif reminder_type == "dec15":

        heading = (
            f"⚠️ {target_year} "
            "ANNUAL GIFT PREP — FINAL PACKING CHECK"
        )

        full_checklist = False

    elif reminder_type == "dec25":

        heading = (
            f"🚨 {target_year} "
            "ANNUAL GIFT PREP — FINAL REMINDER"
        )

        full_checklist = False

    else:

        await message.reply_text(
            "❌ Unknown reminder type."
        )

        return

    text = build_annual_prep_reminder_text(
        target_year,
        heading,
        full_checklist=full_checklist,
    )

    if text is None:

        await message.reply_text(
            f"✅ {target_year} Annual Gift Prep "
            "is already fully completed."
        )

        return

    sent = await send_care_birthday_message(
        context,
        text,
    )

    if sent:

        await message.reply_text(
            "✅ Annual Gift Prep test reminder "
            "sent to the CARE Birthday destination."
        )

    else:

        await message.reply_text(
            "❌ Test reminder could not be sent."
        )


# =========================================================
# BUTTON CALLBACKS
# =========================================================

async def handle_care_birthday_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle CARE Birthday buttons."""

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
            "to manage CARE Birthdays."
        )

        return

    callback_data = (
        query.data
        or ""
    )

    # -----------------------------------------------------
    # CONTROL PANEL → CURRENT BATCH
    # -----------------------------------------------------

    if (
        callback_data
        == "panel:care:birthday:comingsoon:batch"
    ):

        year, month = (
            get_current_care_birthday_period()
        )

        await query.edit_message_text(
            format_care_birthday_batch(
                year,
                month,
            ),
            reply_markup=build_batch_view_keyboard(
                year,
                month,
            ),
        )

        return

    # -----------------------------------------------------
    # CONTROL PANEL → CHECKLIST
    # -----------------------------------------------------

    if (
        callback_data
        == "panel:care:birthday:comingsoon:checklist"
    ):

        year, month = (
            get_current_care_birthday_period()
        )

        await query.edit_message_text(
            format_care_birthday_batch(
                year,
                month,
            ),
            reply_markup=build_checklist_keyboard(
                year,
                month,
            ),
        )

        return

    # -----------------------------------------------------
    # CONTROL PANEL → ANNUAL GIFT PREP
    # -----------------------------------------------------

    if (
        callback_data
        == "panel:care:birthday:annual"
    ):

        target_year = (
            get_current_annual_prep_year()
        )

        await query.edit_message_text(
            format_care_annual_prep(
                target_year
            ),
            reply_markup=build_annual_prep_keyboard(
                target_year
            ),
        )

        return

    # -----------------------------------------------------
    # CONFIRM / CANCEL ROSTER REMOVAL
    # -----------------------------------------------------

    if callback_data.startswith(
        "carebirthday:removeconfirm:"
    ):

        member_id = int(
            callback_data.split(
                ":"
            )[2]
        )

        member = get_care_birthday_member_by_id(
            member_id
        )

        if (
            member is None
            or not member.is_active
        ):
            await query.edit_message_text(
                "❌ This birthday member is already inactive "
                "or no longer exists."
            )
            return

        removed = deactivate_care_birthday_member(
            member_id
        )

        if removed is None:
            await query.edit_message_text(
                "❌ The birthday member could not be removed."
            )
            return

        await query.edit_message_text(
            "✅ CARE BIRTHDAY REMOVED\n\n"
            f"{removed.display_name} has been removed "
            "from the active CARE Birthday roster.\n\n"
            "Their historical workflow records are retained."
        )
        return

    if callback_data == "carebirthday:removecancel":

        await query.edit_message_text(
            "✅ Birthday removal cancelled."
        )
        return

    # -----------------------------------------------------
    # VIEW MONTHLY BATCH
    # -----------------------------------------------------

    if callback_data.startswith(
        "carebirthday:view:"
    ):

        parts = callback_data.split(
            ":"
        )

        year = int(
            parts[2]
        )

        month = int(
            parts[3]
        )

        await query.edit_message_text(
            format_care_birthday_batch(
                year,
                month,
            ),
            reply_markup=build_batch_view_keyboard(
                year,
                month,
            ),
        )

        return

    # -----------------------------------------------------
    # MONTHLY CHECKLIST
    # -----------------------------------------------------

    if callback_data.startswith(
        "carebirthday:checklist:"
    ):

        parts = callback_data.split(
            ":"
        )

        year = int(
            parts[2]
        )

        month = int(
            parts[3]
        )

        await query.edit_message_text(
            format_care_birthday_batch(
                year,
                month,
            ),
            reply_markup=build_checklist_keyboard(
                year,
                month,
            ),
        )

        return

    # -----------------------------------------------------
    # TOGGLE MONTHLY ITEM
    # -----------------------------------------------------

    if callback_data.startswith(
        "carebirthday:toggle:"
    ):

        parts = callback_data.split(
            ":"
        )

        year = int(
            parts[2]
        )

        month = int(
            parts[3]
        )

        item_key = parts[4]

        toggle_care_birthday_checklist_item(
            year,
            month,
            item_key,
        )

        await query.edit_message_text(
            format_care_birthday_batch(
                year,
                month,
            ),
            reply_markup=build_checklist_keyboard(
                year,
                month,
            ),
        )

        return

    # -----------------------------------------------------
    # VIEW ANNUAL GIFT PREP
    # -----------------------------------------------------

    if callback_data.startswith(
        "carebirthday:annual:"
    ):

        parts = callback_data.split(
            ":"
        )

        target_year = int(
            parts[2]
        )

        await query.edit_message_text(
            format_care_annual_prep(
                target_year
            ),
            reply_markup=build_annual_prep_keyboard(
                target_year
            ),
        )

        return

    # -----------------------------------------------------
    # TOGGLE ANNUAL GIFT PREP ITEM
    # -----------------------------------------------------

    if callback_data.startswith(
        "carebirthday:annualtoggle:"
    ):

        parts = callback_data.split(
            ":"
        )

        target_year = int(
            parts[2]
        )

        item_key = parts[3]

        toggle_care_annual_prep_item(
            target_year,
            item_key,
        )

        await query.edit_message_text(
            format_care_annual_prep(
                target_year
            ),
            reply_markup=build_annual_prep_keyboard(
                target_year
            ),
        )

        return


# =========================================================
# REGISTER HANDLERS
# =========================================================

def register_care_birthday_handlers(
    application: Application,
) -> None:
    """Register CARE Birthday commands and scheduler."""

    application.add_handler(
        CommandHandler(
            "setupcarebirthdays",
            setup_care_birthdays_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "carebirthdayroster",
            care_birthday_roster_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "addcarebirthday",
            add_care_birthday_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "removecarebirthday",
            remove_care_birthday_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "carebirthdaymonth",
            care_birthday_month_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "carebirthdaybatch",
            care_birthday_batch_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "carebirthdaychecklist",
            care_birthday_checklist_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "careannualprep",
            care_annual_prep_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runcarebirthdaycheck",
            run_care_birthday_check_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "testcarebirthdayreminder",
            test_care_birthday_reminder_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "testcareannualreminder",
            test_care_annual_reminder_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_care_birthday_callback,
            pattern=(
                r"^(?:"
                r"panel:care:birthday:"
                r"(?:comingsoon:(?:batch|checklist)|annual)"
                r"|carebirthday:"
                r")"
            ),
        )
    )

    if not CARE_BIRTHDAY_SCHEDULER_ENABLED:

        logger.info(
            "CARE Birthday scheduler is disabled."
        )

        return

    if application.job_queue is None:

        logger.error(
            "JobQueue unavailable. "
            "CARE Birthday scheduler not started."
        )

        return

    application.job_queue.run_daily(
        scheduled_care_birthday_job,
        time=time(
            hour=10,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        name="care_birthday_daily_check",
    )

    logger.info(
        "CARE Birthday scheduler enabled: "
        "daily at 10:00 AM Singapore time."
    )