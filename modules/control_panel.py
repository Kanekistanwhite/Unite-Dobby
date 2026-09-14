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
from modules.care_birthdays import (
    is_care_leader,
    setup_care_birthdays_command,
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

CARE_PANEL_TEXT = (
    "❤️ CARE TEAM\n\n"
    "Which CARE faction would you like to manage?"
)

CARE_BIRTHDAY_PANEL_TEXT = (
    "🎂 CARE — BIRTHDAYS\n\n"
    "Manage the Youth Ministry birthday workflow."
)


# ---------------------------------------------------------
# ACCESS
# ---------------------------------------------------------

def has_any_panel_access(
    user_id: int | None,
) -> bool:
    """Check whether the user has access to any workspace."""

    return (
        is_approved_leader(user_id)
        or is_events_leader(user_id)
        or is_care_leader(user_id)
    )


# ---------------------------------------------------------
# MAIN WORKSPACE MENU
# ---------------------------------------------------------

def build_workspace_menu(
    user_id: int | None,
) -> InlineKeyboardMarkup:
    """Build the main Dobby workspace menu."""

    keyboard = []

    if is_approved_leader(user_id):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🏠 UNITE",
                    callback_data="panel:workspace:unite",
                )
            ]
        )

    if is_events_leader(user_id):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🎉 EVENTS TEAM",
                    callback_data="panel:workspace:events",
                )
            ]
        )

    if is_care_leader(user_id):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "❤️ CARE TEAM",
                    callback_data="panel:workspace:care",
                )
            ]
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
    """Create the UNITE control panel."""

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
    """Create a back button for Events."""

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
# CARE MENU
# ---------------------------------------------------------

def build_care_menu() -> InlineKeyboardMarkup:
    """Create the CARE Team faction menu."""

    keyboard = [
        [
            InlineKeyboardButton(
                "🎂 Birthdays",
                callback_data="panel:care:birthdays",
            ),
        ],
        [
            InlineKeyboardButton(
                "👋 Newcomers",
                callback_data="panel:care:comingsoon:newcomers",
            ),
            InlineKeyboardButton(
                "🏆 Milestones",
                callback_data="panel:care:comingsoon:milestones",
            ),
        ],
        [
            InlineKeyboardButton(
                "💌 Encouragement",
                callback_data="panel:care:comingsoon:encouragement",
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
# CARE BIRTHDAY MENU
# ---------------------------------------------------------

def build_care_birthday_menu() -> InlineKeyboardMarkup:
    """Create the CARE Birthday control panel."""

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 View Birthday Month",
                callback_data="panel:care:birthday:viewmonth",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 Sync Birthday Roster",
                callback_data="panel:care:birthday:sync",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Current Batch",
                callback_data="panel:care:birthday:comingsoon:batch",
            ),
            InlineKeyboardButton(
                "✅ Update Checklist",
                callback_data="panel:care:birthday:comingsoon:checklist",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 Distribution",
                callback_data="panel:care:birthday:comingsoon:distribution",
            ),
            InlineKeyboardButton(
                "🔔 Send Reminder",
                callback_data="panel:care:birthday:comingsoon:reminder",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to CARE",
                callback_data="panel:workspace:care",
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


def build_care_birthday_back_menu() -> InlineKeyboardMarkup:
    """Create a back button for CARE Birthday."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back to Birthdays",
                    callback_data="panel:care:birthdays",
                )
            ]
        ]
    )


# ---------------------------------------------------------
# UNITE CONFIRMATION
# ---------------------------------------------------------

def build_confirmation_menu(
    action_name: str,
) -> InlineKeyboardMarkup:
    """Create confirmation buttons for UNITE actions."""

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
    """Open Dobby's control panel."""

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
    """Run a UNITE information action."""

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
    """Show Events Team schedule."""

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
    """Handle all Dobby control-panel buttons."""

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
    # MAIN
    # -----------------------------------------------------

    if callback_data == "panel:open":
        await query.edit_message_text(
            CONTROL_PANEL_TEXT,
            reply_markup=build_workspace_menu(
                user_id
            ),
        )
        return

    if callback_data == "panel:close":
        await query.edit_message_text(
            "✅ Dobby's control panel has been closed.\n\n"
            "Send /menu to open it again."
        )
        return

    # -----------------------------------------------------
    # UNITE
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
    # EVENTS
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
    # CARE
    # -----------------------------------------------------

    if callback_data == "panel:workspace:care":

        if not is_care_leader(
            user_id
        ):
            await query.edit_message_text(
                "⛔ You do not have permission "
                "to manage CARE Team."
            )
            return

        await query.edit_message_text(
            CARE_PANEL_TEXT,
            reply_markup=build_care_menu(),
        )
        return

    # -----------------------------------------------------
    # CARE — BIRTHDAYS
    # -----------------------------------------------------

    if callback_data == "panel:care:birthdays":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            CARE_BIRTHDAY_PANEL_TEXT,
            reply_markup=build_care_birthday_menu(),
        )
        return

    # -----------------------------------------------------
    # CARE — VIEW BIRTHDAY MONTH
    # -----------------------------------------------------

    if callback_data == "panel:care:birthday:viewmonth":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "📅 VIEW BIRTHDAY MONTH\n\n"
            "Send:\n\n"
            "/carebirthdaymonth MM-YYYY\n\n"
            "Example:\n"
            "/carebirthdaymonth 10-2026\n\n"
            "Dobby will show:\n"
            "• All birthday celebrants\n"
            "• Their birthday dates\n"
            "• Number of celebrants\n"
            "• First-Sunday celebration date",
            reply_markup=build_care_birthday_back_menu(),
        )
        return

    # -----------------------------------------------------
    # CARE — SYNC BIRTHDAY ROSTER
    # -----------------------------------------------------

    if callback_data == "panel:care:birthday:sync":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "⏳ Syncing CARE Birthday roster..."
        )

        await setup_care_birthdays_command(
            update,
            context,
        )

        await query.edit_message_text(
            CARE_BIRTHDAY_PANEL_TEXT,
            reply_markup=build_care_birthday_menu(),
        )
        return

    # -----------------------------------------------------
    # CARE — COMING SOON BIRTHDAY FEATURES
    # -----------------------------------------------------

    if callback_data.startswith(
        "panel:care:birthday:comingsoon:"
    ):

        await query.edit_message_text(
            "🚧 This CARE Birthday feature "
            "is being built next.\n\n"
            "The birthday roster and monthly "
            "celebrant view are already working.",
            reply_markup=build_care_birthday_back_menu(),
        )
        return

    # -----------------------------------------------------
    # CARE — OTHER FACTIONS
    # -----------------------------------------------------

    if callback_data.startswith(
        "panel:care:comingsoon:"
    ):

        faction = callback_data.split(
            ":"
        )[-1]

        names = {
            "newcomers": "👋 Newcomers",
            "milestones": "🏆 Milestones",
            "encouragement": "💌 Encouragement",
        }

        faction_name = names.get(
            faction,
            "CARE faction",
        )

        await query.edit_message_text(
            f"{faction_name}\n\n"
            "🚧 This CARE workflow has not been "
            "built yet.\n\n"
            "We are building CARE in this order:\n"
            "🎂 Birthdays\n"
            "👋 Newcomers\n"
            "🏆 Milestones\n"
            "💌 Encouragement",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back to CARE",
                            callback_data="panel:workspace:care",
                        )
                    ]
                ]
            ),
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
            "🔔 Automatic reminders:\n"
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
            "🔔 Automatic reminders:\n"
            "• 3 days before at 10:00 AM\n"
            "• Deadline day at 10:00 AM",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # EVENTS — REMINDER
    # -----------------------------------------------------

    if callback_data == "panel:events:reminder":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "🔔 SEND MEETING REMINDER\n\n"
            "First check 📋 View Schedule.\n\n"
            "Then send:\n\n"
            "/sendeventreminder ID\n\n"
            "Example:\n"
            "/sendeventreminder 3\n\n"
            "This does not affect automatic reminders.",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # EVENTS — COMPLETE
    # -----------------------------------------------------

    if callback_data == "panel:events:complete":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "✅ COMPLETE DEADLINE\n\n"
            "Send:\n\n"
            "/completeevent ID\n\n"
            "Example:\n"
            "/completeevent 2",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # EVENTS — CANCEL
    # -----------------------------------------------------

    if callback_data == "panel:events:cancel":

        if not is_events_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "❌ CANCEL EVENTS ITEM\n\n"
            "Send:\n\n"
            "/cancelevent ID\n\n"
            "Example:\n"
            "/cancelevent 3",
            reply_markup=build_events_back_menu(),
        )
        return

    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    await query.edit_message_text(
        "❌ That control-panel option is no longer available.",
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