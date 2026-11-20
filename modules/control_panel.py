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

from services.care_encouragement_service import (
    format_active_encouragement_batches,
    format_encouragement_annual_plan,
    format_encouragement_month,
    get_singapore_today as get_encouragement_today,
)
from services.care_milestone_service import (
    format_active_milestones,
    format_milestone_annual_plan,
    format_milestone_history,
    format_month_milestones,
    format_year_milestones,
    get_singapore_today as get_milestone_today,
)
from services.care_newcomer_service import (
    format_newcomer_inventory,
    format_newcomer_register,
    get_singapore_today as get_newcomer_today,
)
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

CARE_NEWCOMER_PANEL_TEXT = (
    "👋 CARE — NEWCOMERS\n\n"
    "Manage newcomer registration and newcomer-pack stock."
)

CARE_MILESTONE_PANEL_TEXT = (
    "🏆 CARE — MILESTONES\n\n"
    "Manage milestone celebrations, gifts and cards."
)

CARE_ENCOURAGEMENT_PANEL_TEXT = (
    "💌 CARE — ENCOURAGEMENT\n\n"
    "Manage encouragement periods, packs, cards and packing."
)


# ---------------------------------------------------------
# ACCESS
# ---------------------------------------------------------

def has_any_panel_access(
    user_id: int | None,
) -> bool:
    """Check whether user has access to any workspace."""

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
    """Build main Dobby workspace menu."""

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
    """Create UNITE control panel."""

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
    """Create Events Team control panel."""

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
    """Create Events back button."""

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
    """Create CARE faction menu."""

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
                callback_data="panel:care:newcomers",
            ),
            InlineKeyboardButton(
                "🏆 Milestones",
                callback_data="panel:care:milestones",
            ),
        ],
        [
            InlineKeyboardButton(
                "💌 Encouragement",
                callback_data="panel:care:encouragement",
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
    """Create CARE Birthday control panel."""

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 View Birthday Month",
                callback_data="panel:care:birthday:viewmonth",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Birthday Roster",
                callback_data="panel:care:birthday:roster",
            ),
        ],
        [
            InlineKeyboardButton(
                "➕ Add Birthday",
                callback_data="panel:care:birthday:add",
            ),
            InlineKeyboardButton(
                "🗑 Remove Birthday",
                callback_data="panel:care:birthday:remove",
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
                "🎁 Annual Gift Prep",
                callback_data="panel:care:birthday:annual",
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
# CARE NEWCOMER MENU
# ---------------------------------------------------------

def build_care_newcomer_menu() -> InlineKeyboardMarkup:
    """Create CARE Newcomer control panel."""

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Register Newcomer",
                callback_data="panel:care:newcomer:add",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔎 Find Newcomer",
                callback_data="panel:care:newcomer:find",
            ),
            InlineKeyboardButton(
                "📋 Newcomer Register",
                callback_data="panel:care:newcomer:register",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 Pack Inventory",
                callback_data="panel:care:newcomer:stock",
            ),
        ],
        [
            InlineKeyboardButton(
                "🧮 Set Physical Stock",
                callback_data="panel:care:newcomer:setstock",
            ),
            InlineKeyboardButton(
                "➕ Add Replenishment",
                callback_data="panel:care:newcomer:addstock",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎁 Give Outstanding Pack",
                callback_data="panel:care:newcomer:givepack",
            ),
        ],
        [
            InlineKeyboardButton(
                "↩️ Remove Newcomer",
                callback_data="panel:care:newcomer:remove",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎁 Annual Pack Prep",
                callback_data="panel:care:newcomer:annual",
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


def build_care_newcomer_back_menu() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back to Newcomers",
                    callback_data="panel:care:newcomers",
                )
            ]
        ]
    )


# ---------------------------------------------------------
# CARE MILESTONE MENU
# ---------------------------------------------------------

def build_care_milestone_menu() -> InlineKeyboardMarkup:
    """Create CARE Milestone control panel."""

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add Milestone",
                callback_data="panel:care:milestone:add",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Active Milestones",
                callback_data="panel:care:milestone:active",
            ),
            InlineKeyboardButton(
                "📅 This Month",
                callback_data="panel:care:milestone:month",
            ),
        ],
        [
            InlineKeyboardButton(
                "🗓 Year Tracker",
                callback_data="panel:care:milestone:year",
            ),
            InlineKeyboardButton(
                "🎁 Annual Planning",
                callback_data="panel:care:milestone:plan",
            ),
        ],
        [
            InlineKeyboardButton(
                "✏️ Update Date",
                callback_data="panel:care:milestone:updatedate",
            ),
            InlineKeyboardButton(
                "📚 History",
                callback_data="panel:care:milestone:history",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel Milestone",
                callback_data="panel:care:milestone:cancel",
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


def build_care_milestone_back_menu() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back to Milestones",
                    callback_data="panel:care:milestones",
                )
            ]
        ]
    )


# ---------------------------------------------------------
# CARE ENCOURAGEMENT MENU
# ---------------------------------------------------------

def build_care_encouragement_menu() -> InlineKeyboardMarkup:
    """Create CARE Encouragement control panel."""

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add Encouragement Period",
                callback_data="panel:care:encouragement:add",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Active Batches",
                callback_data="panel:care:encouragement:active",
            ),
            InlineKeyboardButton(
                "🗓 This Month",
                callback_data="panel:care:encouragement:month",
            ),
        ],
        [
            InlineKeyboardButton(
                "👥 Manage Recipients",
                callback_data="panel:care:encouragement:recipients",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 Set Packing Date",
                callback_data="panel:care:encouragement:packing",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎁 Annual Preparation",
                callback_data="panel:care:encouragement:annual",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel Batch",
                callback_data="panel:care:encouragement:cancel",
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


def build_care_encouragement_back_menu() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Back to Encouragement",
                    callback_data="panel:care:encouragement",
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

    return InlineKeyboardMarkup(
        [
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
    )


def get_confirmation_text(
    action_name: str,
) -> str:

    messages = {
        "sunday": (
            "⛪ SEND SUNDAY POLL\n\n"
            "Are you sure you want Dobby to send "
            "the Sunday attendance poll now?"
        ),
        "biweekly": (
            "🏠 RUN BI-WEEKLY CHECK\n\n"
            "Are you sure you want Dobby to check "
            "for pending bi-weekly attendance polls?"
        ),
        "birthday": (
            "🎂 RUN BIRTHDAY CHECK\n\n"
            "Are you sure you want Dobby to check "
            "for today's birthdays?"
        ),
        "planning": (
            "🎁 RUN PLANNING CHECK\n\n"
            "Are you sure you want Dobby to check "
            "for pending birthday-planning reminders?"
        ),
    }

    return messages.get(
        action_name,
        "Are you sure?",
    )


# ---------------------------------------------------------
# /MENU
# ---------------------------------------------------------

async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

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
# UNITE ACTIONS
# ---------------------------------------------------------

async def run_unite_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action_name: str,
) -> None:

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
        return

    handlers = {
        "sunday": run_sunday_check_command,
        "biweekly": run_biweekly_check_command,
        "birthday": run_birthday_check_command,
        "planning": run_birthday_planning_check_command,
    }

    handler = handlers.get(
        action_name
    )

    if handler is None:
        return

    await query.edit_message_text(
        "⏳ Dobby is running the requested action..."
    )

    await handler(
        update,
        context,
    )

    await query.edit_message_text(
        UNITE_PANEL_TEXT,
        reply_markup=build_unite_menu(),
    )


async def run_unite_display_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action_name: str,
) -> None:

    query = update.callback_query
    user = update.effective_user

    if query is None:
        return

    user_id = (
        user.id
        if user
        else None
    )

    handlers = {
        "biweekly": list_biweekly_command,
        "members": list_members_command,
        "chatid": chat_id,
        "topicid": topic_id,
        "myid": my_id,
    }

    handler = handlers.get(
        action_name
    )

    if handler is None:
        return

    await handler(
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
    """Handle Dobby panel buttons."""

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
            return

        await query.edit_message_text(
            CARE_PANEL_TEXT,
            reply_markup=build_care_menu(),
        )

        return

    # =====================================================
    # CARE BIRTHDAYS
    # =====================================================

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

    if callback_data == "panel:care:birthday:viewmonth":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "📅 VIEW BIRTHDAY MONTH\n\n"
            "Send:\n"
            "/carebirthdaymonth MM-YYYY\n\n"
            "Example:\n"
            "/carebirthdaymonth 10-2026",
            reply_markup=build_care_birthday_back_menu(),
        )

        return

    if callback_data == "panel:care:birthday:roster":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "📋 BIRTHDAY ROSTER\n\n"
            "Send:\n"
            "/carebirthdayroster\n\n"
            "Dobby will list every active CARE Birthday member "
            "in calendar order.",
            reply_markup=build_care_birthday_back_menu(),
        )

        return

    if callback_data == "panel:care:birthday:add":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "➕ ADD CARE BIRTHDAY\n\n"
            "Send:\n"
            "/addcarebirthday NAME | DD-MM\n\n"
            "Example:\n"
            "/addcarebirthday John Tan | 14-03\n\n"
            "Dobby will reject duplicate active names "
            "and validate the birthday date.",
            reply_markup=build_care_birthday_back_menu(),
        )

        return

    if callback_data == "panel:care:birthday:remove":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            "🗑 REMOVE CARE BIRTHDAY\n\n"
            "Send:\n"
            "/removecarebirthday NAME\n\n"
            "Example:\n"
            "/removecarebirthday John Tan\n\n"
            "Dobby will show the matching birthday and ask "
            "for confirmation before removing them.",
            reply_markup=build_care_birthday_back_menu(),
        )

        return

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

    if callback_data.startswith(
        "panel:care:birthday:comingsoon:"
    ):

        await query.edit_message_text(
            "🎂 CARE Birthday workflow\n\n"
            "Use the Birthday checklist to manage this batch.",
            reply_markup=build_care_birthday_back_menu(),
        )

        return

    # =====================================================
    # CARE NEWCOMERS
    # =====================================================

    if callback_data == "panel:care:newcomers":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            CARE_NEWCOMER_PANEL_TEXT,
            reply_markup=build_care_newcomer_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:add":

        await query.edit_message_text(
            "➕ REGISTER NEWCOMER\n\n"
            "Send:\n"
            "/addnewcomer NAME | INVITED BY\n\n"
            "Example:\n"
            "/addnewcomer John Tan | Gordon",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:find":

        await query.edit_message_text(
            "🔎 FIND NEWCOMER\n\n"
            "Send:\n"
            "/findnewcomer NAME",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:register":

        await query.edit_message_text(
            format_newcomer_register(),
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:stock":

        year = (
            get_newcomer_today().year
        )

        await query.edit_message_text(
            format_newcomer_inventory(
                year
            ),
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:setstock":

        await query.edit_message_text(
            "🧮 SET PHYSICAL STOCK\n\n"
            "Send:\n"
            "/setnewcomerstock QUANTITY [YEAR]\n\n"
            "Example:\n"
            "/setnewcomerstock 34",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:addstock":

        await query.edit_message_text(
            "➕ ADD REPLENISHMENT\n\n"
            "Send:\n"
            "/addnewcomerstock QUANTITY [YEAR]\n\n"
            "Example:\n"
            "/addnewcomerstock 20",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:givepack":

        await query.edit_message_text(
            "🎁 GIVE OUTSTANDING PACK\n\n"
            "Send:\n"
            "/givepack NAME",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:remove":

        await query.edit_message_text(
            "↩️ REMOVE NEWCOMER\n\n"
            "Send:\n"
            "/removenewcomer NAME\n\n"
            "Dobby will ask for confirmation first.",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:annual":

        target_year = (
            get_newcomer_today().year + 1
        )

        await query.edit_message_text(
            "🎁 ANNUAL NEWCOMER PACK PREP\n\n"
            f"Send:\n/carenewcomerprep {target_year}",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    # =====================================================
    # CARE MILESTONES
    # =====================================================

    if callback_data == "panel:care:milestones":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            CARE_MILESTONE_PANEL_TEXT,
            reply_markup=build_care_milestone_menu(),
        )

        return

    if callback_data == "panel:care:milestone:add":

        await query.edit_message_text(
            "➕ ADD MILESTONE\n\n"
            "Send:\n"
            "/addmilestone NAME | TYPE | DATE\n\n"
            "Example:\n"
            "/addmilestone John Tan | university | "
            "18-05-2027\n\n"
            "Month only:\n"
            "/addmilestone John Tan | university | "
            "05-2027",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    if callback_data == "panel:care:milestone:active":

        await query.edit_message_text(
            format_active_milestones(),
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    if callback_data == "panel:care:milestone:month":

        today = get_milestone_today()

        await query.edit_message_text(
            format_month_milestones(
                today.year,
                today.month,
            ),
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    if callback_data == "panel:care:milestone:year":

        today = get_milestone_today()

        await query.edit_message_text(
            format_year_milestones(
                today.year
            ),
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    if callback_data == "panel:care:milestone:plan":

        target_year = (
            get_milestone_today().year + 1
        )

        await query.edit_message_text(
            format_milestone_annual_plan(
                target_year
            )
            + "\n\n"
            f"Open checklist:\n"
            f"/milestoneplan {target_year}\n\n"
            "Set gift:\n"
            "/setmilestonegift YEAR | TYPE | GIFT",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    if callback_data == "panel:care:milestone:updatedate":

        await query.edit_message_text(
            "✏️ UPDATE MILESTONE DATE\n\n"
            "Send:\n"
            "/updatemilestonedate ID | DD-MM-YYYY\n\n"
            "Example:\n"
            "/updatemilestonedate 3 | 18-05-2027",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    if callback_data == "panel:care:milestone:history":

        today = get_milestone_today()

        await query.edit_message_text(
            format_milestone_history(
                today.year
            ),
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    if callback_data == "panel:care:milestone:cancel":

        await query.edit_message_text(
            "❌ CANCEL MILESTONE\n\n"
            "Send:\n"
            "/cancelmilestone ID confirm",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # =====================================================
    # CARE ENCOURAGEMENT
    # =====================================================

    if callback_data == "panel:care:encouragement":

        if not is_care_leader(
            user_id
        ):
            return

        await query.edit_message_text(
            CARE_ENCOURAGEMENT_PANEL_TEXT,
            reply_markup=build_care_encouragement_menu(),
        )

        return

    # -----------------------------------------------------
    # ADD ENCOURAGEMENT PERIOD
    # -----------------------------------------------------

    if callback_data == "panel:care:encouragement:add":

        await query.edit_message_text(
            "➕ ADD ENCOURAGEMENT PERIOD\n\n"
            "Send:\n"
            "/addencouragement TITLE | PERIOD\n\n"
            "Month-only example:\n"
            "/addencouragement Mid-Year Exams | 06-2027\n\n"
            "Date-range example:\n"
            "/addencouragement O Level Exams | "
            "20-10-2027 to 10-11-2027",
            reply_markup=build_care_encouragement_back_menu(),
        )

        return

    # -----------------------------------------------------
    # ACTIVE BATCHES
    # -----------------------------------------------------

    if callback_data == "panel:care:encouragement:active":

        await query.edit_message_text(
            format_active_encouragement_batches(),
            reply_markup=build_care_encouragement_back_menu(),
        )

        return

    # -----------------------------------------------------
    # THIS MONTH
    # -----------------------------------------------------

    if callback_data == "panel:care:encouragement:month":

        today = get_encouragement_today()

        await query.edit_message_text(
            format_encouragement_month(
                today.year,
                today.month,
            ),
            reply_markup=build_care_encouragement_back_menu(),
        )

        return

    # -----------------------------------------------------
    # MANAGE RECIPIENTS
    # -----------------------------------------------------

    if callback_data == "panel:care:encouragement:recipients":

        await query.edit_message_text(
            "👥 MANAGE RECIPIENTS\n\n"
            "Add someone:\n"
            "/addencouragementrecipient BATCH_ID | NAME\n\n"
            "View batch recipients:\n"
            "/encouragementrecipients BATCH_ID\n\n"
            "Open one person's checklist:\n"
            "/encouragementrecipient RECIPIENT_ID\n\n"
            "Remove someone:\n"
            "/removeencouragementrecipient "
            "RECIPIENT_ID confirm",
            reply_markup=build_care_encouragement_back_menu(),
        )

        return

    # -----------------------------------------------------
    # SET PACKING DATE
    # -----------------------------------------------------

    if callback_data == "panel:care:encouragement:packing":

        await query.edit_message_text(
            "📦 SET PACKING DATE\n\n"
            "Send:\n"
            "/setencouragementpacking "
            "BATCH_ID | DD-MM-YYYY\n\n"
            "Example:\n"
            "/setencouragementpacking 2 | 12-06-2027\n\n"
            "Dobby will remind CARE:\n"
            "• 1 week before\n"
            "• 1 day before",
            reply_markup=build_care_encouragement_back_menu(),
        )

        return

    # -----------------------------------------------------
    # ANNUAL PREPARATION
    # -----------------------------------------------------

    if callback_data == "panel:care:encouragement:annual":

        target_year = (
            get_encouragement_today().year + 1
        )

        await query.edit_message_text(
            format_encouragement_annual_plan(
                target_year
            )
            + "\n\n"
            "Open the interactive checklist:\n"
            f"/encouragementplan {target_year}",
            reply_markup=build_care_encouragement_back_menu(),
        )

        return

    # -----------------------------------------------------
    # CANCEL BATCH
    # -----------------------------------------------------

    if callback_data == "panel:care:encouragement:cancel":

        await query.edit_message_text(
            "❌ CANCEL ENCOURAGEMENT BATCH\n\n"
            "First view active batches:\n"
            "/activeencouragement\n\n"
            "Then send:\n"
            "/cancelencouragement BATCH_ID confirm",
            reply_markup=build_care_encouragement_back_menu(),
        )

        return

    # =====================================================
    # UNITE CONFIRMATIONS
    # =====================================================

    if callback_data.startswith(
        "panel:confirm:"
    ):

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

    # =====================================================
    # EVENTS
    # =====================================================

    if callback_data == "panel:events:schedule":

        await show_events_schedule(
            update,
            context,
        )

        return

    if callback_data == "panel:events:addmeeting":

        await query.edit_message_text(
            "➕ ADD EVENTS MEETING\n\n"
            "Send:\n"
            "/addeventmeeting DD-MM-YYYY HH:MM | Meeting Name",
            reply_markup=build_events_back_menu(),
        )

        return

    if callback_data == "panel:events:adddeadline":

        await query.edit_message_text(
            "➕ ADD EVENTS DEADLINE\n\n"
            "Send:\n"
            "/addeventdeadline DD-MM-YYYY | Deadline Name",
            reply_markup=build_events_back_menu(),
        )

        return

    if callback_data == "panel:events:reminder":

        await query.edit_message_text(
            "🔔 SEND MEETING REMINDER\n\n"
            "Send:\n"
            "/sendeventreminder ID",
            reply_markup=build_events_back_menu(),
        )

        return

    if callback_data == "panel:events:complete":

        await query.edit_message_text(
            "✅ COMPLETE DEADLINE\n\n"
            "Send:\n"
            "/completeevent ID",
            reply_markup=build_events_back_menu(),
        )

        return

    if callback_data == "panel:events:cancel":

        await query.edit_message_text(
            "❌ CANCEL EVENTS ITEM\n\n"
            "Send:\n"
            "/cancelevent ID",
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
    """Register Dobby control panel."""

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