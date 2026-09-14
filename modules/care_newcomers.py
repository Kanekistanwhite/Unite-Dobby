import logging
from datetime import time
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
    CARE_NEWCOMER_CHAT_ID,
    CARE_NEWCOMER_SCHEDULER_ENABLED,
    CARE_NEWCOMER_TOPIC_ID,
)
from services.care_newcomer_service import (
    NEWCOMER_ANNUAL_PREP_CHECKLIST,
    add_newcomer_stock,
    build_midyear_stocktake_reminder,
    build_newcomer_annual_reminder,
    find_newcomer,
    format_newcomer_annual_prep,
    format_newcomer_inventory,
    format_newcomer_record,
    format_newcomer_register,
    get_current_newcomer_prep_year,
    get_or_create_newcomer_annual_prep,
    get_singapore_today,
    give_pack_to_newcomer,
    mark_midyear_reminder_sent,
    mark_newcomer_annual_reminder_sent,
    midyear_reminder_was_sent,
    newcomer_annual_reminder_was_sent,
    register_newcomer,
    remove_newcomer,
    set_newcomer_stock,
    toggle_newcomer_annual_prep_item,
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
    """Check whether user is approved CARE leader."""

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
# ANNUAL PREP KEYBOARD
# =========================================================

def build_newcomer_annual_prep_keyboard(
    target_year: int,
) -> InlineKeyboardMarkup:
    """Build interactive annual prep checklist."""

    prep = get_or_create_newcomer_annual_prep(
        target_year
    )

    labels = {
        "contents": "📋 Contents Confirmed",
        "quantity": "🔢 Quantity Confirmed",
        "items": "🛒 Items Purchased",
        "packaging": "📦 Packaging Purchased",
        "arrived": "📥 All Items Received",
        "packed": "🎁 Packs Packed",
        "stock": "✅ Final Stock Confirmed",
    }

    keyboard = []

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in NEWCOMER_ANNUAL_PREP_CHECKLIST.items():

        done = getattr(
            prep,
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
                        "carenewcomer:annualtoggle:"
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

async def send_care_newcomer_message(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> bool:
    """Send Newcomer reminder to configured topic."""

    if CARE_NEWCOMER_CHAT_ID is None:

        logger.error(
            "CARE_NEWCOMER_CHAT_ID is not configured."
        )

        return False

    kwargs = {}

    if CARE_NEWCOMER_TOPIC_ID is not None:

        kwargs[
            "message_thread_id"
        ] = CARE_NEWCOMER_TOPIC_ID

    try:

        await context.bot.send_message(
            chat_id=CARE_NEWCOMER_CHAT_ID,
            text=text,
            **kwargs,
        )

        return True

    except Exception:

        logger.exception(
            "CARE Newcomer reminder could not be sent."
        )

        return False


# =========================================================
# AUTOMATIC REMINDERS
# =========================================================

async def send_due_care_newcomer_reminders(
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Send Newcomer reminders due today."""

    today = get_singapore_today()

    sent_count = 0

    # -----------------------------------------------------
    # MID-YEAR STOCKTAKE — 1 JULY
    # -----------------------------------------------------

    if (
        today.month == 7
        and today.day == 1
    ):

        if not midyear_reminder_was_sent(
            today.year
        ):

            sent = await send_care_newcomer_message(
                context,
                build_midyear_stocktake_reminder(
                    today.year
                ),
            )

            if sent:

                mark_midyear_reminder_sent(
                    today.year
                )

                sent_count += 1

    # -----------------------------------------------------
    # ANNUAL PREP — NOVEMBER / DECEMBER
    # -----------------------------------------------------

    target_year = (
        today.year + 1
    )

    heading = None
    reminder_flag = None
    full_checklist = False

    if (
        today.month == 11
        and today.day == 1
    ):

        heading = (
            f"👋 {target_year} "
            "NEWCOMER PACK PREPARATION"
        )

        reminder_flag = (
            "open_reminder_sent"
        )

        full_checklist = True

    elif (
        today.month == 11
        and today.day == 15
    ):

        heading = (
            f"🔔 {target_year} NEWCOMER PACK "
            "PREP PROGRESS CHECK"
        )

        reminder_flag = (
            "nov15_reminder_sent"
        )

    elif (
        today.month == 12
        and today.day == 1
    ):

        heading = (
            f"🔔 {target_year} NEWCOMER PACK "
            "PREP — DECEMBER CHECK"
        )

        reminder_flag = (
            "dec1_reminder_sent"
        )

    elif (
        today.month == 12
        and today.day == 15
    ):

        heading = (
            f"⚠️ {target_year} NEWCOMER PACK "
            "PREP — FINAL PACKING CHECK"
        )

        reminder_flag = (
            "dec15_reminder_sent"
        )

    elif (
        today.month == 12
        and today.day == 25
    ):

        heading = (
            f"🚨 {target_year} NEWCOMER PACK "
            "PREP — FINAL REMINDER"
        )

        reminder_flag = (
            "dec25_reminder_sent"
        )

    if (
        heading is not None
        and reminder_flag is not None
    ):

        if not newcomer_annual_reminder_was_sent(
            target_year,
            reminder_flag,
        ):

            text = build_newcomer_annual_reminder(
                target_year,
                heading,
                full_checklist=full_checklist,
            )

            if text is not None:

                sent = await send_care_newcomer_message(
                    context,
                    text,
                )

                if sent:

                    mark_newcomer_annual_reminder_sent(
                        target_year,
                        reminder_flag,
                    )

                    sent_count += 1

    return sent_count


async def scheduled_care_newcomer_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Run daily Newcomer scheduler."""

    logger.info(
        "Running CARE Newcomer reminder check."
    )

    sent_count = (
        await send_due_care_newcomer_reminders(
            context
        )
    )

    logger.info(
        "CARE Newcomer check complete. "
        "%s reminder(s) sent.",
        sent_count,
    )


# =========================================================
# EXISTING NEWCOMER COMMANDS
# =========================================================

async def add_newcomer_command(
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

    if "|" not in raw_text:

        await message.reply_text(
            "Usage:\n"
            "/addnewcomer NAME | INVITED BY\n\n"
            "Example:\n"
            "/addnewcomer John Tan | Gordon"
        )

        return

    newcomer_name, invited_by = (
        raw_text.split(
            "|",
            maxsplit=1,
        )
    )

    newcomer_name = newcomer_name.strip()
    invited_by = invited_by.strip()

    try:

        (
            status,
            newcomer,
            inventory,
        ) = register_newcomer(
            newcomer_name,
            invited_by,
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    if status == "duplicate":

        await message.reply_text(
            "⚠️ NEWCOMER ALREADY REGISTERED\n\n"
            f"{format_newcomer_record(newcomer)}\n\n"
            "🚫 Do not issue another newcomer pack.\n\n"
            "📝 Please verify that this person is "
            "already recorded in the CARE Newcomer "
            "Master Sheet."
        )

        return

    if status == "registered":

        response = (
            "✅ NEWCOMER REGISTERED\n\n"
            f"👋 Name: {newcomer.display_name}\n"
            f"🙋 Invited by: {newcomer.invited_by}\n"
            f"📅 First visit: "
            f"{newcomer.first_visit_date.strftime('%d %b %Y')}\n"
            "🎁 Newcomer pack: ✅ Given\n\n"
            f"📦 Packs remaining: "
            f"{inventory.current_stock}\n\n"
            "📝 REMINDER:\n"
            f"Please remember to add "
            f"{newcomer.display_name} into the "
            "CARE Newcomer Master Sheet."
        )

        if (
            inventory.current_stock
            <= inventory.low_stock_threshold
        ):

            response += (
                "\n\n⚠️ LOW STOCK WARNING\n"
                f"Only {inventory.current_stock} "
                "newcomer pack(s) remain."
            )

        await message.reply_text(
            response
        )

        return

    await message.reply_text(
        "✅ NEWCOMER REGISTERED\n\n"
        f"👋 Name: {newcomer.display_name}\n"
        f"🙋 Invited by: {newcomer.invited_by}\n"
        "🎁 Newcomer pack: ❌ NOT GIVEN\n\n"
        "🚨 There are no newcomer packs left.\n\n"
        f"After replenishing use:\n"
        f"/givepack {newcomer.display_name}\n\n"
        "📝 Remember to add this person to the "
        "CARE Newcomer Master Sheet."
    )


async def find_newcomer_command(
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

    name = " ".join(
        context.args
    ).strip()

    if not name:

        await message.reply_text(
            "Usage:\n/findnewcomer NAME"
        )

        return

    newcomer = find_newcomer(
        name
    )

    if newcomer is None:

        await message.reply_text(
            f"🔎 No record found for:\n{name}"
        )

        return

    await message.reply_text(
        "🔎 NEWCOMER FOUND\n\n"
        f"{format_newcomer_record(newcomer)}"
    )


async def newcomer_register_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    await update.effective_message.reply_text(
        format_newcomer_register()
    )


async def newcomer_stock_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    year = get_singapore_today().year

    if context.args:

        try:
            year = int(
                context.args[0]
            )

        except ValueError:

            await update.effective_message.reply_text(
                "❌ Invalid year."
            )

            return

    await update.effective_message.reply_text(
        format_newcomer_inventory(
            year
        )
    )


async def set_newcomer_stock_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if not context.args:

        await message.reply_text(
            "Usage:\n"
            "/setnewcomerstock QUANTITY [YEAR]"
        )

        return

    try:

        quantity = int(
            context.args[0]
        )

        year = (
            int(context.args[1])
            if len(context.args) >= 2
            else get_singapore_today().year
        )

        inventory = set_newcomer_stock(
            year,
            quantity,
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        "✅ NEWCOMER STOCK UPDATED\n\n"
        f"Year: {year}\n"
        f"Current physical stock: "
        f"{inventory.current_stock}"
    )


async def add_newcomer_stock_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if not context.args:

        await message.reply_text(
            "Usage:\n"
            "/addnewcomerstock QUANTITY [YEAR]"
        )

        return

    try:

        quantity = int(
            context.args[0]
        )

        year = (
            int(context.args[1])
            if len(context.args) >= 2
            else get_singapore_today().year
        )

        inventory = add_newcomer_stock(
            year,
            quantity,
        )

    except ValueError as error:

        await message.reply_text(
            f"❌ {error}"
        )

        return

    await message.reply_text(
        "✅ NEWCOMER STOCK REPLENISHED\n\n"
        f"Added: {quantity} packs\n"
        f"Current stock: "
        f"{inventory.current_stock}"
    )


async def give_pack_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    name = " ".join(
        context.args
    ).strip()

    if not name:

        await message.reply_text(
            "Usage:\n/givepack NAME"
        )

        return

    (
        status,
        newcomer,
        inventory,
    ) = give_pack_to_newcomer(
        name
    )

    if status == "not_found":

        await message.reply_text(
            "❌ Newcomer not found."
        )

        return

    if status == "already_given":

        await message.reply_text(
            "⚠️ This newcomer already received a pack."
        )

        return

    if status == "no_stock":

        await message.reply_text(
            "🚨 No newcomer packs available."
        )

        return

    await message.reply_text(
        "✅ NEWCOMER PACK GIVEN\n\n"
        f"👋 {newcomer.display_name}\n"
        f"📦 Packs remaining: "
        f"{inventory.current_stock}"
    )


async def remove_newcomer_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    raw_text = " ".join(
        context.args
    ).strip()

    if not raw_text:

        await message.reply_text(
            "Usage:\n/removenewcomer NAME"
        )

        return

    confirmed = False

    if "|" in raw_text:

        name_part, confirmation_part = (
            raw_text.rsplit(
                "|",
                maxsplit=1,
            )
        )

        name = name_part.strip()

        confirmed = (
            confirmation_part.strip().lower()
            == "confirm"
        )

    else:

        name = raw_text.strip()

    newcomer = find_newcomer(
        name
    )

    if newcomer is None:

        await message.reply_text(
            "❌ Newcomer not found."
        )

        return

    if not confirmed:

        restore_text = (
            "📦 1 pack will be restored."
            if newcomer.pack_given
            else "📦 No stock adjustment."
        )

        await message.reply_text(
            "⚠️ REMOVE NEWCOMER?\n\n"
            f"{format_newcomer_record(newcomer)}\n\n"
            f"{restore_text}\n\n"
            "Confirm with:\n"
            f"/removenewcomer "
            f"{newcomer.display_name} | confirm"
        )

        return

    (
        status,
        removed_name,
        pack_restored,
        inventory,
    ) = remove_newcomer(
        name
    )

    if status != "removed":

        await message.reply_text(
            "❌ Could not remove newcomer."
        )

        return

    text = (
        "✅ NEWCOMER REMOVED\n\n"
        f"👋 {removed_name}"
    )

    if (
        pack_restored
        and inventory is not None
    ):

        text += (
            "\n\n📦 Pack restored."
            f"\nCurrent stock: "
            f"{inventory.current_stock}"
        )

    await message.reply_text(
        text
    )


# =========================================================
# ANNUAL PREP COMMAND
# =========================================================

async def newcomer_annual_prep_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    if context.args:

        try:
            target_year = int(
                context.args[0]
            )

        except ValueError:

            await update.effective_message.reply_text(
                "❌ Invalid year."
            )

            return

    else:

        target_year = (
            get_current_newcomer_prep_year()
        )

    await update.effective_message.reply_text(
        format_newcomer_annual_prep(
            target_year
        ),
        reply_markup=(
            build_newcomer_annual_prep_keyboard(
                target_year
            )
        ),
    )


# =========================================================
# MANUAL SCHEDULER CHECK
# =========================================================

async def run_newcomer_check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    count = (
        await send_due_care_newcomer_reminders(
            context
        )
    )

    await update.effective_message.reply_text(
        "👋 CARE Newcomer reminder check complete.\n\n"
        f"{count} reminder(s) sent."
    )


# =========================================================
# TEST REMINDER
# =========================================================

async def test_newcomer_reminder_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if len(context.args) != 2:

        await message.reply_text(
            "Usage:\n"
            "/testcarenewcomerreminder TYPE YEAR\n\n"
            "Types:\n"
            "open\n"
            "nov15\n"
            "dec1\n"
            "dec15\n"
            "dec25\n"
            "midyear\n\n"
            "Example:\n"
            "/testcarenewcomerreminder open 2027"
        )

        return

    reminder_type = (
        context.args[0]
        .strip()
        .lower()
    )

    try:
        year = int(
            context.args[1]
        )

    except ValueError:

        await message.reply_text(
            "❌ Invalid year."
        )

        return

    if reminder_type == "midyear":

        text = build_midyear_stocktake_reminder(
            year
        )

    else:

        headings = {
            "open": (
                f"👋 {year} NEWCOMER PACK PREPARATION"
            ),
            "nov15": (
                f"🔔 {year} NEWCOMER PACK "
                "PREP PROGRESS CHECK"
            ),
            "dec1": (
                f"🔔 {year} NEWCOMER PACK "
                "PREP — DECEMBER CHECK"
            ),
            "dec15": (
                f"⚠️ {year} NEWCOMER PACK "
                "PREP — FINAL PACKING CHECK"
            ),
            "dec25": (
                f"🚨 {year} NEWCOMER PACK "
                "PREP — FINAL REMINDER"
            ),
        }

        heading = headings.get(
            reminder_type
        )

        if heading is None:

            await message.reply_text(
                "❌ Unknown reminder type."
            )

            return

        text = build_newcomer_annual_reminder(
            year,
            heading,
            full_checklist=(
                reminder_type == "open"
            ),
        )

        if text is None:

            await message.reply_text(
                f"✅ {year} newcomer pack preparation "
                "is already completed."
            )

            return

    sent = await send_care_newcomer_message(
        context,
        text,
    )

    if sent:

        await message.reply_text(
            "✅ Test reminder sent to "
            "CARE Newcomer proxy topic."
        )

    else:

        await message.reply_text(
            "❌ Test reminder could not be sent."
        )


# =========================================================
# ANNUAL CHECKLIST CALLBACKS
# =========================================================

async def handle_newcomer_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

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
            "to manage CARE Newcomers."
        )

        return

    callback_data = (
        query.data
        or ""
    )

    if callback_data.startswith(
        "carenewcomer:annualtoggle:"
    ):

        parts = callback_data.split(
            ":"
        )

        target_year = int(
            parts[2]
        )

        item_key = parts[3]

        toggle_newcomer_annual_prep_item(
            target_year,
            item_key,
        )

        await query.edit_message_text(
            format_newcomer_annual_prep(
                target_year
            ),
            reply_markup=(
                build_newcomer_annual_prep_keyboard(
                    target_year
                )
            ),
        )


# =========================================================
# REGISTER
# =========================================================

def register_care_newcomer_handlers(
    application: Application,
) -> None:
    """Register CARE Newcomer system."""

    application.add_handler(
        CommandHandler(
            "addnewcomer",
            add_newcomer_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "findnewcomer",
            find_newcomer_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "newcomerregister",
            newcomer_register_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "newcomerstock",
            newcomer_stock_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "setnewcomerstock",
            set_newcomer_stock_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "addnewcomerstock",
            add_newcomer_stock_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "givepack",
            give_pack_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "removenewcomer",
            remove_newcomer_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "carenewcomerprep",
            newcomer_annual_prep_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "runcarenewcomercheck",
            run_newcomer_check_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "testcarenewcomerreminder",
            test_newcomer_reminder_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_newcomer_callback,
            pattern=r"^carenewcomer:",
        )
    )

    if not CARE_NEWCOMER_SCHEDULER_ENABLED:

        logger.info(
            "CARE Newcomer scheduler is disabled."
        )

        return

    if application.job_queue is None:

        logger.error(
            "JobQueue unavailable. "
            "CARE Newcomer scheduler not started."
        )

        return

    application.job_queue.run_daily(
        scheduled_care_newcomer_job,
        time=time(
            hour=10,
            minute=0,
            tzinfo=SINGAPORE_TIMEZONE,
        ),
        name="care_newcomer_daily_check",
    )

    logger.info(
        "CARE Newcomer scheduler enabled: "
        "daily at 10:00 AM Singapore time."
    )