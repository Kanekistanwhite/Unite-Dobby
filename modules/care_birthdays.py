from datetime import datetime

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

from config.settings import CARE_LEADER_USER_IDS
from services.care_birthday_service import (
    CARE_BIRTHDAY_CHECKLIST,
    format_care_birthday_batch,
    format_care_birthday_month,
    get_current_care_birthday_period,
    get_or_create_care_birthday_batch,
    seed_care_birthday_roster,
    toggle_care_birthday_checklist_item,
)


def is_care_leader(
    user_id: int | None,
) -> bool:
    """Check whether a user may manage CARE Team."""

    if user_id is None:
        return False

    return user_id in CARE_LEADER_USER_IDS


async def check_care_permission(
    update: Update,
) -> bool:
    """Allow only approved CARE Team leaders."""

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


def build_batch_view_keyboard(
    year: int,
    month: int,
) -> InlineKeyboardMarkup:
    """Buttons shown underneath the batch summary."""

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
    """Create interactive CARE Birthday checklist buttons."""

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
    }

    for (
        item_key,
        (
            field_name,
            label,
        ),
    ) in CARE_BIRTHDAY_CHECKLIST.items():

        completed = getattr(
            batch,
            field_name,
        )

        status_icon = (
            "✅"
            if completed
            else "⬜"
        )

        button_text = (
            f"{status_icon} "
            f"{button_labels[item_key]}"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=(
                        f"carebirthday:toggle:"
                        f"{year}:{month}:{item_key}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "📋 View Batch",
                callback_data=(
                    f"carebirthday:view:"
                    f"{year}:{month}"
                ),
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back to Birthdays",
                callback_data="panel:care:birthdays",
            )
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


def parse_month_year(
    value: str,
) -> tuple[int, int]:
    """Convert MM-YYYY into year and month."""

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


async def setup_care_birthdays_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Load or update the CARE Birthday roster."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "⏳ Updating CARE Birthday roster..."
    )

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
    """Show birthdays for a selected month."""

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
            "/carebirthdaymonth MM-YYYY\n\n"
            "Example:\n"
            "/carebirthdaymonth 10-2026"
        )
        return

    try:
        year, month = parse_month_year(
            context.args[0]
        )

    except (
        ValueError,
        TypeError,
    ):
        await message.reply_text(
            "❌ Invalid month.\n\n"
            "Please use MM-YYYY.\n\n"
            "Example:\n"
            "/carebirthdaymonth 10-2026"
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
    """Show the current or selected Birthday batch."""

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

        except (
            ValueError,
            TypeError,
        ):
            await message.reply_text(
                "❌ Invalid month.\n\n"
                "Please use MM-YYYY.\n\n"
                "Example:\n"
                "/carebirthdaybatch 10-2026"
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
    """Open the interactive Birthday preparation checklist."""

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

        except (
            ValueError,
            TypeError,
        ):
            await message.reply_text(
                "❌ Invalid month.\n\n"
                "Please use MM-YYYY."
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
        reply_markup=build_checklist_keyboard(
            year,
            month,
        ),
    )


async def handle_care_birthday_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle CARE Birthday batch/checklist buttons."""

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

    # Current Batch button from CARE control panel.
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

    # Update Checklist button from CARE control panel.
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

    # View a specific batch.
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

    # Open checklist for a specific batch.
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

    # Toggle one checklist item.
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

        try:
            toggle_care_birthday_checklist_item(
                year,
                month,
                item_key,
            )

        except ValueError as error:
            await query.edit_message_text(
                f"❌ {error}"
            )
            return

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


def register_care_birthday_handlers(
    application: Application,
) -> None:
    """Register CARE Birthday commands and buttons."""

    application.add_handler(
        CommandHandler(
            "setupcarebirthdays",
            setup_care_birthdays_command,
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
        CallbackQueryHandler(
            handle_care_birthday_callback,
            pattern=(
                r"^(?:"
                r"panel:care:birthday:comingsoon:"
                r"(?:batch|checklist)"
                r"|carebirthday:"
                r")"
            ),
        )
    )