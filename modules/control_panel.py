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
from modules.events import (
    events_schedule_command,
    is_events_leader,
)
from modules.members import list_members_command
from modules.sunday import run_sunday_check_command
from services.permissions import is_approved_leader


# ---------------------------------------------------------
# PANEL TEXT
# ---------------------------------------------------------

CONTROL_PANEL_TEXT = (
    "🧰 DOBBY CONTROL PANEL\n\n"
    "Which team would you like to manage?"
)

UNITE_PANEL_TEXT = (
    "🏠 UNITE\n\n"
    "Choose what you would like Dobby to do:"
)

EVENTS_PANEL_TEXT = (
    "🎉 ACTS EVENTS TEAM\n\n"
    "Choose what you would like Dobby to do:"
)


# ---------------------------------------------------------
# ACCESS
# ---------------------------------------------------------

def has_any_panel_access(
    user_id: int | None,
) -> bool:
    """Check whether the user has access to any Dobby workspace."""

    return (
        is_approved_leader(user_id)
        or is_events_leader(user_id)
    )


# ---------------------------------------------------------
# MAIN WORKSPACE MENU
# ---------------------------------------------------------

def build_workspace_menu(
    user_id: int | None,
) -> InlineKeyboardMarkup:
    """Build the workspace-selection menu."""

    keyboard = []

    workspace_row = []

    if is_approved_leader(user_id):
        workspace_row.append(
            InlineKeyboardButton(
                "🏠 UNITE",
                callback_data="panel:workspace:unite",
            )
        )

    if is_events_leader(user_id):
        workspace_row.append(
            InlineKeyboardButton(
                "🎉 EVENTS TEAM",
                callback_data="panel:workspace:events",
            )
        )

    if workspace_row:
        keyboard.append(
            workspace_row
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "👤 My ID",
                callback_data="panel:show:myid",
            ),
            InlineKeyboardButton(
                "❌ Close",
                callback_data="panel:close",
            ),
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# ---------------------------------------------------------
# UNITE MENU
# ---------------------------------------------------------

def build_unite_menu() -> InlineKeyboardMarkup:
    """Create the UNITE leader control panel."""

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
                "⬅️ Back",
                callback_data="panel:open",
            ),
            InlineKeyboardButton(
                "❌ Close",
                callback_data="panel:close",
            ),
        ],
    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ---------------------------------------------------------
# EVENTS MENU
# ---------------------------------------------------------

def build_events_menu() -> InlineKeyboardMarkup:
    """Create the Events Team control panel."""

    keyboard = [
        [
            InlineKeyboardButton(
                "📋 View Schedule",
                callback_data="panel:events:schedule",
            ),
        ],
        [
            InlineKeyboardButton(
                "➕ Add Meeting",
                callback_data="panel:events:addmeeting",
            ),
            InlineKeyboardButton(
                "➕ Add Deadline",
                callback_data="panel:events:adddeadline",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔔 Send Reminder",
                callback_data="panel:events:reminder",
            ),
        ],
        [
            InlineKeyboardButton(
                "✅ Complete Deadline",
                callback_data="panel:events:complete",
            ),
            InlineKeyboardButton(
                "❌ Cancel Item",
                callback_data="panel:events:cancel",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="panel:open",
            ),
            InlineKeyboardButton(
                "❌ Close",
                callback_data="panel:close",
            ),
        ],
    ]

    return InlineKeyboardMarkup(
        keyboard
    )


def build_events_back_menu() -> InlineKeyboardMarkup:
    """Create a back button for Events Team instructions."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back to Events",
                    callback_data="panel:workspace:events",
                )
            ]
        ]
    )


# ---------------------------------------------------------
# UNITE CONFIRMATION MENU
# ---------------------------------------------------------

def build_confirmation_menu(
    action_name: str,
) -> InlineKeyboardMarkup:
    """Create confirmation buttons for a UNITE action."""

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm",
                callback_data=f"panel:run:{action_name}",
            ),
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="panel:workspace:unite",
            ),
        ]
    ]

    return InlineKeyboardMarkup(
        keyboard
    )


def get_confirmation_text(
    action_name: str,
) -> str:
    """Return confirmation text for a UNITE action."""

    confirmation_messages = {
        "sunday": (
            "⛪ SEND SUNDAY POLL\n\n"
            "Are you sure you want Dobby to send "
            "the Sunday attendance poll now?\n\n"
            "A poll may be sent to the UNITE group."
        ),
        "biweekly": (
            "🏠 RUN BI-WEEKLY CHECK\n\n"
            "Are you sure you want Dobby to check "
            "for pending bi-weekly attendance polls?"
        ),
        "birthday": (
            "🎂 RUN BIRTHDAY CHECK\n\n"
            "Are you sure you want Dobby to check "
            "for today's birthdays?\n\n"
            "A birthday greeting may be sent "
            "to the UNITE group."
        ),
        "planning": (
            "🎁 RUN PLANNING CHECK\n\n"
            "Are you sure you want Dobby to check "
            "for pending birthday-planning reminders?"
        ),
    }

    return confirmation_messages.get(
        action_name,
        "Are you sure you want to run this action?",
    )


# ---------------------------------------------------------
# /MENU
# ---------------------------------------------------------

async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Open Dobby's workspace control panel."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return

    user_id = (
        user.id
        if user
        else None
    )

    if not has_any_panel_access(
        user_id
    ):
        await message.reply_text(
            "⛔ This control panel is only available "
            "to approved leaders."
        )
        return

    await message.reply_text(
        CONTROL_PANEL_TEXT,
        reply_markup=build_workspace_menu(
            user_id
        ),
    )


# ---------------------------------------------------------
# RUN UNITE ACTION
# ---------------------------------------------------------

async def run_unite_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action_name: str,
) -> None:
    """Run a confirmed UNITE action."""

    query = update.callback_query
    user = update.effective_user

    if query is None:
        return

    user_id = (
        user.id
        if user
        else None
    )

    if not is_approved_leader(
        user_id
    ):
        await query.edit_message_text(
            "⛔ You do not have permission "
            "to manage UNITE."
        )
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
            "❌ That action could not be found."
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
        UNITE_PANEL_TEXT,
        reply_markup=build_unite_menu(),
    )


# ---------------------------------------------------------
# DISPLAY UNITE INFORMATION
# ---------------------------------------------------------

async def run_unite_display_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action_name: str,
) -> None:
    """Run an information command for UNITE."""

    query = update.callback_query
    user = update.effective_user

    if query is None:
        return

    user_id = (
        user.id
        if user
        else None
    )

    if (
        action_name != "myid"
        and not is_approved_leader(user_id)
    ):
        await query.edit_message_text(
            "⛔ You do not have permission "
            "to manage UNITE."
        )
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
            "❌ That option could not be found."
        )
        return

    await action_handler(
        update,
        context,
    )

    if action_name == "myid":
        await query.edit_message_text(
            CONTROL_PANEL_TEXT,
            reply_markup=build_workspace_menu(
                user_id
            ),
        )
    else:
        await query.edit_message_text(
            UNITE_PANEL_TEXT,
            reply_markup=build_unite_menu(),
        )


# ---------------------------------------------------------
# EVENTS SCHEDULE
# ---------------------------------------------------------

async def show_events_schedule(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the Events Team schedule."""

    query = update.callback_query
    user = update.effective_user

    if query is None:
        return

    user_id = (
        user.id
        if user
        else None
    )

    if not is_events_leader(
        user_id
    ):
        await query.edit_message_text(
            "⛔ You do not have permission "
            "to manage Events Team."
        )
        return

    await events_schedule_command(
        update,
        context,
    )

    await query.edit_message_text(
        EVENTS_PANEL_TEXT,
        reply_markup=build_events_menu(),
    )


# ---------------------------------------------------------
# CALLBACK HANDLER
# ---------------------------------------------------------

async def handle_control_panel_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle all Dobby control-panel button presses."""

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

    if not has_any_panel_access(
        user_id
    ):
        await query.edit_message_text(
            "⛔ This control panel is only available "
            "to approved leaders."
        )
        return

    callback_data = (
        query.data
        or ""
    )

    # -----------------------------------------------------
    # MAIN MENU
    # -----------------------------------------------------

    if callback_data == "panel:open":
        await query.edit_message_text(
            CONTROL_PANEL_TEXT,
            reply_markup=build_workspace_menu(
                user_id
            ),
        )
        return

    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------

    if callback_data == "panel:close":
        await query.edit_message_text(
            "✅ Dobby's control panel has been closed.\n\n"
            "Send /menu to open it again."
        )
        return

    # -----------------------------------------------------
    # WORKSPACE: UNITE
    # -----------------------------------------------------

    if callback_data == "panel:workspace:unite":

        if not is_approved_leader(
            user_id
        ):
            await query.edit_message_text(
                "⛔ You do not have permission "
                "to manage UNITE."
            )
            return

        await query.edit_message_text(
            UNITE_PANEL_TEXT,
            reply_markup=build_unite_menu(),
        )
        return

    # -----------------------------------------------------
    # WORKSPACE: EVENTS TEAM
    # -----------------------------------------------------

    if callback_data == "panel:workspace:events":

        if not is_events_leader(
            user_id
        ):
            await query.edit_message_text(
                "⛔ You do not have permission "
                "to manage Events Team."
            )
            return

        await query.edit_message_text(
            EVENTS_PANEL_TEXT,
            reply_markup=build_events_menu(),
        )
        return

    # -----------------------------------------------------
    # UNITE CONFIRMATIONS
    # -----------------------------------------------------

    if callback_data.startswith(
        "panel:confirm:"
    ):
        if not is_approved_leader(
            user_id
        ):
            await query.edit_message_text(
                "⛔ You do not have permission "
                "to manage UNITE."
            )
            return

        action_name = callback_data.split(
            ":",
            maxsplit=2,
        )[2]

        await query.edit_message_text(
            get_confirmation_text(
                action_name
            ),
            reply_markup=build_confirmation_menu(
                action_name
            ),
        )
        return

    # -----------------------------------------------------
    # RUN UNITE ACTION
    # -----------------------------------------------------

    if callback_data.startswith(
        "panel:run:"
    ):
        action_name = callback_data.split(
            ":",
            maxsplit=2,
        )[2]

        await run_unite_action(
            update,
            context,
            action_name,
        )
        return

    # -----------------------------------------------------
    # UNITE INFORMATION
    # -----------------------------------------------------

    if callback_data.startswith(
        "panel:show:"
    ):
        action_name = callback_data.split(
            ":",
            maxsplit=2,
        )[2]

        await run_unite_display_action(
            update,
            context,
            action_name,
        )
        return

    # -----------------------------------------------------
    # EVENTS — VIEW SCHEDULE
    # -----------------------------------------------------

    if callback_data == "panel:events:schedule":

        await show_events_schedule(
            update,
            context,
        )
        return

    # -----------------------------------------------------
    # EVENTS — ADD MEETING
    # -----------------------------------------------------

    if callback_data == "panel:events:addmeeting":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "➕ ADD EVENTS MEETING\n\n"
            "Send:\n\n"
            "/addeventmeeting DD-MM-YYYY HH:MM | Meeting Name\n\n"
            "Example:\n"
            "/addeventmeeting 15-09-2026 20:00 | "
            "September Events Meeting\n\n"
            "🔔 Dobby will automatically remind the team:\n"
            "• 1 week before at 10:00 AM\n"
            "• 1 day before at 10:00 AM",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # EVENTS — ADD DEADLINE
    # -----------------------------------------------------

    if callback_data == "panel:events:adddeadline":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "➕ ADD EVENTS DEADLINE\n\n"
            "Send:\n\n"
            "/addeventdeadline DD-MM-YYYY | Deadline Name\n\n"
            "Example:\n"
            "/addeventdeadline 25-09-2026 | "
            "Finalise Event Proposal\n\n"
            "🔔 Dobby will automatically remind the team:\n"
            "• 3 days before at 10:00 AM\n"
            "• Deadline day at 10:00 AM",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # EVENTS — SEND MANUAL REMINDER
    # -----------------------------------------------------

    if callback_data == "panel:events:reminder":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "🔔 SEND MEETING REMINDER\n\n"
            "First press 📋 View Schedule to find "
            "the meeting ID.\n\n"
            "Then send:\n\n"
            "/sendeventreminder ID\n\n"
            "Example:\n"
            "/sendeventreminder 3\n\n"
            "Dobby will immediately send a reminder "
            "to the Events Team group.\n\n"
            "✅ This does NOT affect the automatic "
            "1-week or 1-day reminders.",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # EVENTS — COMPLETE DEADLINE
    # -----------------------------------------------------

    if callback_data == "panel:events:complete":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "✅ COMPLETE DEADLINE\n\n"
            "First press 📋 View Schedule to find "
            "the deadline ID.\n\n"
            "Then send:\n\n"
            "/completeevent ID\n\n"
            "Example:\n"
            "/completeevent 2\n\n"
            "Once completed, Dobby will stop sending "
            "reminders for that deadline.",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # EVENTS — CANCEL ITEM
    # -----------------------------------------------------

    if callback_data == "panel:events:cancel":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "❌ CANCEL EVENTS ITEM\n\n"
            "First press 📋 View Schedule to find "
            "the meeting or deadline ID.\n\n"
            "Then send:\n\n"
            "/cancelevent ID\n\n"
            "Example:\n"
            "/cancelevent 3\n\n"
            "Cancelled items will no longer receive reminders.",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # UNKNOWN CALLBACK
    # -----------------------------------------------------

    await query.edit_message_text(
        "❌ That control-panel option is no longer available.\n\n"
        "Please reopen the menu.",
        reply_markup=build_workspace_menu(
            user_id
        ),
    )


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

def register_control_panel_handlers(
    application: Application,
) -> None:
    """Register Dobby's control-panel handlers."""

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