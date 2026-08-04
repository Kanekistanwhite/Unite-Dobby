from collections.abc import Awaitable, Callable

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
from modules.sunday import run_sunday_check_command
from services.permissions import is_approved_leader


CallbackFunction = Callable[
    [Update, ContextTypes.DEFAULT_TYPE],
    Awaitable[None],
]


CONTROL_PANEL_TEXT = (
    "🧰 UNITE DOBBY CONTROL PANEL\n\n"
    "Choose what you would like Dobby to do.\n\n"
    "Actions that send messages or polls will ask "
    "for confirmation first."
)


def build_main_menu() -> InlineKeyboardMarkup:
    """Build the main leader control panel."""

    keyboard = [
        [
            InlineKeyboardButton(
                "⛪ Sunday Poll",
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
                callback_data="panel:show:listbiweekly",
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
) -> tuple[str, InlineKeyboardMarkup]:
    """Build a confirmation screen for a sending action."""

    confirmation_details = {
        "sunday": (
            "⛪ Send Sunday attendance poll?",
            (
                "This will post the Sunday message and poll "
                "to the configured Telegram topic."
            ),
        ),
        "biweekly": (
            "🏠 Run bi-weekly poll check?",
            (
                "This sends every pending bi-weekly poll "
                "that is currently due."
            ),
        ),
        "birthday": (
            "🎂 Run today’s birthday check?",
            (
                "This may send a birthday greeting to the "
                "main UNITE group when a birthday is due today."
            ),
        ),
        "planning": (
            "🎁 Run today’s planning check?",
            (
                "This may send due birthday-planning reminders "
                "to the private planning group."
            ),
        ),
    }

    title, description = confirmation_details[action_name]

    text = (
        f"{title}\n\n"
        f"{description}\n\n"
        "Continue?"
    )

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

    return text, InlineKeyboardMarkup(keyboard)


def leader_is_approved(
    update: Update,
) -> bool:
    """Check whether the person is an approved leader."""

    user = update.effective_user
    user_id = user.id if user else None

    return is_approved_leader(user_id)


async def show_control_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open the leader control panel using /menu."""

    message = update.effective_message

    if message is None:
        return

    if not leader_is_approved(update):
        await message.reply_text(
            "⛔ The Dobby control panel is only available "
            "to approved leaders."
        )
        return

    await message.reply_text(
        CONTROL_PANEL_TEXT,
        reply_markup=build_main_menu(),
    )


async def run_existing_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action_function: CallbackFunction,
) -> None:
    """Run an existing Dobby command from a button."""

    await action_function(
        update,
        context,
    )


async def handle_control_panel_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle every button inside the control panel."""

    query = update.callback_query

    if query is None:
        return

    if not leader_is_approved(update):
        await query.answer(
            "This control panel is only for approved leaders.",
            show_alert=True,
        )
        return

    await query.answer()

    callback_data = query.data or ""

    if callback_data == "panel:open":
        await query.edit_message_text(
            CONTROL_PANEL_TEXT,
            reply_markup=build_main_menu(),
        )
        return

    if callback_data == "panel:close":
        if query.message is not None:
            await query.message.delete()
        return

    if callback_data.startswith("panel:confirm:"):
        action_name = callback_data.removeprefix(
            "panel:confirm:"
        )

        if action_name not in {
            "sunday",
            "biweekly",
            "birthday",
            "planning",
        }:
            await query.edit_message_text(
                "❌ Unknown control-panel action."
            )
            return

        text, keyboard = build_confirmation_menu(
            action_name
        )

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
        )
        return

    sending_actions: dict[str, CallbackFunction] = {
        "panel:run:sunday": run_sunday_check_command,
        "panel:run:biweekly": run_biweekly_check_command,
        "panel:run:birthday": run_birthday_check_command,
        (
            "panel:run:planning"
        ): run_birthday_planning_check_command,
    }

    selected_sending_action = sending_actions.get(
        callback_data
    )

    if selected_sending_action is not None:
        await query.edit_message_text(
            "⏳ Running Dobby action..."
        )

        await run_existing_action(
            update=update,
            context=context,
            action_function=selected_sending_action,
        )

        await query.edit_message_text(
            CONTROL_PANEL_TEXT,
            reply_markup=build_main_menu(),
        )
        return

    information_actions: dict[str, CallbackFunction] = {
        "panel:show:listbiweekly": list_biweekly_command,
        "panel:show:chatid": chat_id,
        "panel:show:topicid": topic_id,
        "panel:show:myid": my_id,
    }

    selected_information_action = information_actions.get(
        callback_data
    )

    if selected_information_action is not None:
        await run_existing_action(
            update=update,
            context=context,
            action_function=selected_information_action,
        )
        return

    await query.edit_message_text(
        "❌ Unknown control-panel action.",
        reply_markup=build_main_menu(),
    )


def register_control_panel_handlers(
    application: Application,
) -> None:
    """Register the leader control panel."""

    application.add_handler(
        CommandHandler(
            "menu",
            show_control_panel,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_control_panel_callback,
            pattern=r"^panel:",
        )
    )