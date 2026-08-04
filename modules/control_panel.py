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

from modules.admin import (
    chat_id,
    my_id,
    topic_id,
)
from modules.birthdays import (
    run_birthday_check_command,
    run_birthday_planning_check_command,
)
from modules.biweekly import (
    list_biweekly_command,
    run_biweekly_check_command,
)
from modules.members import list_members_command
from modules.sunday import run_sunday_check_command
from services.permissions import is_approved_leader


CONTROL_PANEL_TEXT = (
    "🧰 UNITE DOBBY — LEADER CONTROL PANEL\n\n"
    "Choose what you would like Dobby to do:"
)


def build_main_menu() -> InlineKeyboardMarkup:
    """Create the main leader control-panel buttons."""

    keyboard = [
        [
            InlineKeyboardButton(
                "⛪ Send Sunday Poll",
                callback_data="panel:confirm:sunday",
            ),
            InlineKeyboardButton(
                "🏠 Bi-weekly Check",
                callback_data="panel:confirm:biweekly",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎂 Birthday Check",
                callback_data="panel:confirm:birthday",
            ),
            InlineKeyboardButton(
                "🎁 Planning Check",
                callback_data="panel:confirm:planning",
            ),
        ],
        [
            InlineKeyboardButton(
                "📅 List Bi-weekly",
                callback_data="panel:show:biweekly",
            ),
            InlineKeyboardButton(
                "👥 List Members",
                callback_data="panel:show:members",
            ),
        ],
        [
            InlineKeyboardButton(
                "💬 Chat ID",
                callback_data="panel:show:chatid",
            ),
            InlineKeyboardButton(
                "🧵 Topic ID",
                callback_data="panel:show:topicid",
            ),
        ],
        [
            InlineKeyboardButton(
                "👤 My ID",
                callback_data="panel:show:myid",
            ),
            InlineKeyboardButton(
                "❌ Close",
                callback_data="panel:close",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def build_confirmation_menu(
    action_name: str,
) -> InlineKeyboardMarkup:
    """Create confirmation buttons for an action."""

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm",
                callback_data=f"panel:run:{action_name}",
            ),
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="panel:open",
            ),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_confirmation_text(
    action_name: str,
) -> str:
    """Return the confirmation message for an action."""

    confirmation_messages = {
        "sunday": (
            "⛪ SEND SUNDAY POLL\n\n"
            "Are you sure you want Dobby to run the Sunday "
            "attendance check now?\n\n"
            "A poll may be sent to the UNITE group."
        ),
        "biweekly": (
            "🏠 RUN BI-WEEKLY CHECK\n\n"
            "Are you sure you want Dobby to check for pending "
            "bi-weekly attendance polls now?"
        ),
        "birthday": (
            "🎂 RUN BIRTHDAY CHECK\n\n"
            "Are you sure you want Dobby to check for today's "
            "birthdays now?\n\n"
            "A birthday greeting may be sent to the UNITE group."
        ),
        "planning": (
            "🎁 RUN PLANNING CHECK\n\n"
            "Are you sure you want Dobby to check for pending "
            "birthday-planning reminders now?"
        ),
    }

    return confirmation_messages.get(
        action_name,
        "Are you sure you want to run this action?",
    )


async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open the leader control panel."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return

    user_id = user.id if user else None

    if not is_approved_leader(user_id):
        await message.reply_text(
            "⛔ This control panel is only available "
            "to approved leaders."
        )
        return

    await message.reply_text(
        CONTROL_PANEL_TEXT,
        reply_markup=build_main_menu(),
    )


async def run_confirmed_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action_name: str,
) -> None:
    """Run a confirmed control-panel action."""

    query = update.callback_query

    if query is None:
        return

    action_handlers = {
        "sunday": run_sunday_check_command,
        "biweekly": run_biweekly_check_command,
        "birthday": run_birthday_check_command,
        "planning": run_birthday_planning_check_command,
    }

    action_handler = action_handlers.get(
        action_name
    )

    if action_handler is None:
        await query.edit_message_text(
            "❌ That action could not be found.",
            reply_markup=build_main_menu(),
        )
        return

    await query.edit_message_text(
        "⏳ Dobby is running the requested action..."
    )

    await action_handler(
        update,
        context,
    )

    await query.edit_message_text(
        CONTROL_PANEL_TEXT,
        reply_markup=build_main_menu(),
    )


async def run_display_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action_name: str,
) -> None:
    """Run an information-display action."""

    query = update.callback_query

    if query is None:
        return

    action_handlers = {
        "biweekly": list_biweekly_command,
        "members": list_members_command,
        "chatid": chat_id,
        "topicid": topic_id,
        "myid": my_id,
    }

    action_handler = action_handlers.get(
        action_name
    )

    if action_handler is None:
        await query.edit_message_text(
            "❌ That option could not be found.",
            reply_markup=build_main_menu(),
        )
        return

    await action_handler(
        update,
        context,
    )

    await query.edit_message_text(
        CONTROL_PANEL_TEXT,
        reply_markup=build_main_menu(),
    )


async def handle_control_panel_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle all control-panel button presses."""

    query = update.callback_query
    user = update.effective_user

    if query is None:
        return

    await query.answer()

    user_id = user.id if user else None

    if not is_approved_leader(user_id):
        await query.edit_message_text(
            "⛔ This control panel is only available "
            "to approved leaders."
        )
        return

    callback_data = query.data or ""

    if callback_data == "panel:open":
        await query.edit_message_text(
            CONTROL_PANEL_TEXT,
            reply_markup=build_main_menu(),
        )
        return

    if callback_data == "panel:close":
        await query.edit_message_text(
            "✅ UNITE Dobby's control panel has been closed.\n\n"
            "Send /menu to open it again."
        )
        return

    if callback_data.startswith(
        "panel:confirm:"
    ):
        action_name = callback_data.split(
            ":",
            maxsplit=2,
        )[2]

        await query.edit_message_text(
            get_confirmation_text(action_name),
            reply_markup=build_confirmation_menu(
                action_name
            ),
        )
        return

    if callback_data.startswith(
        "panel:run:"
    ):
        action_name = callback_data.split(
            ":",
            maxsplit=2,
        )[2]

        await run_confirmed_action(
            update,
            context,
            action_name,
        )
        return

    if callback_data.startswith(
        "panel:show:"
    ):
        action_name = callback_data.split(
            ":",
            maxsplit=2,
        )[2]

        await run_display_action(
            update,
            context,
            action_name,
        )
        return

    await query.edit_message_text(
        "❌ That control-panel option is no longer available.\n\n"
        "Please reopen the menu.",
        reply_markup=build_main_menu(),
    )


def register_control_panel_handlers(
    application: Application,
) -> None:
    """Register the leader control-panel handlers."""

    application.add_handler(
        CommandHandler(
            "menu",
            menu_command,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_control_panel_callback,
            pattern=r"^panel:",
        )
    )