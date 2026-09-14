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
    """Create Birthday back button."""

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
    """Create Newcomer back button."""

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
    """Create Milestone back button."""

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
# UNITE CONFIRMATION
# ---------------------------------------------------------

def build_confirmation_menu(
    action_name: str,
) -> InlineKeyboardMarkup:
    """Create UNITE confirmation buttons."""

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
    """Return UNITE confirmation text."""

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
    """Open Dobby control panel."""

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

        await query.edit_message_text(
            "📅 VIEW BIRTHDAY MONTH\n\n"
            "Send:\n"
            "/carebirthdaymonth MM-YYYY\n\n"
            "Example:\n"
            "/carebirthdaymonth 10-2026",
            reply_markup=build_care_birthday_back_menu(),
        )

        return

    if callback_data == "panel:care:birthday:sync":

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
            "🚧 This Birthday option is managed by "
            "the CARE Birthday workflow.",
            reply_markup=build_care_birthday_back_menu(),
        )

        return

    # =====================================================
    # CARE NEWCOMERS
    # =====================================================

    if callback_data == "panel:care:newcomers":

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
            "Use this only for an incorrect or test entry.\n\n"
            "Send:\n"
            "/removenewcomer NAME\n\n"
            "Dobby will ask for confirmation before removing.",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    if callback_data == "panel:care:newcomer:annual":

        target_year = (
            get_newcomer_today().year + 1
        )

        await query.edit_message_text(
            "🎁 ANNUAL NEWCOMER PACK PREP\n\n"
            f"Current preparation year: {target_year}\n\n"
            "Send:\n"
            f"/carenewcomerprep {target_year}\n\n"
            "This opens the interactive 50-pack "
            "preparation checklist.",
            reply_markup=build_care_newcomer_back_menu(),
        )

        return

    # =====================================================
    # CARE MILESTONES
    # =====================================================

    if callback_data == "panel:care:milestones":

        await query.edit_message_text(
            CARE_MILESTONE_PANEL_TEXT,
            reply_markup=build_care_milestone_menu(),
        )

        return

    # -----------------------------------------------------
    # ADD MILESTONE
    # -----------------------------------------------------

    if callback_data == "panel:care:milestone:add":

        await query.edit_message_text(
            "➕ ADD MILESTONE\n\n"
            "Send:\n\n"
            "/addmilestone NAME | TYPE | DATE\n\n"
            "Exact date example:\n"
            "/addmilestone John Tan | university | "
            "18-05-2027\n\n"
            "Month-only example:\n"
            "/addmilestone John Tan | university | "
            "05-2027\n\n"
            "Types:\n"
            "🎓 secondary\n"
            "🎓 polytechnic\n"
            "🎓 jc\n"
            "🎓 university\n"
            "✝️ baptism\n"
            "🪖 ord",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # -----------------------------------------------------
    # ACTIVE MILESTONES
    # -----------------------------------------------------

    if callback_data == "panel:care:milestone:active":

        await query.edit_message_text(
            format_active_milestones(),
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # -----------------------------------------------------
    # THIS MONTH
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # YEAR TRACKER
    # -----------------------------------------------------

    if callback_data == "panel:care:milestone:year":

        today = get_milestone_today()

        await query.edit_message_text(
            format_year_milestones(
                today.year
            ),
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # -----------------------------------------------------
    # ANNUAL PLANNING
    # -----------------------------------------------------

    if callback_data == "panel:care:milestone:plan":

        today = get_milestone_today()

        target_year = (
            today.year + 1
        )

        await query.edit_message_text(
            format_milestone_annual_plan(
                target_year
            )
            + "\n\n"
            "To open the interactive lookout checklist:\n"
            f"/milestoneplan {target_year}\n\n"
            "To decide a gift:\n"
            "/setmilestonegift YEAR | TYPE | GIFT\n\n"
            "Example:\n"
            f"/setmilestonegift {target_year} | baptism | "
            "Personalised Bible",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # -----------------------------------------------------
    # UPDATE DATE
    # -----------------------------------------------------

    if callback_data == "panel:care:milestone:updatedate":

        await query.edit_message_text(
            "✏️ UPDATE MILESTONE DATE\n\n"
            "Use this when you initially only knew "
            "the month and later receive the exact date.\n\n"
            "Send:\n"
            "/updatemilestonedate ID | DD-MM-YYYY\n\n"
            "Example:\n"
            "/updatemilestonedate 3 | 18-05-2027\n\n"
            "Once the exact date is added, Dobby can "
            "calculate the 2-week reminder.",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    if callback_data == "panel:care:milestone:history":

        today = get_milestone_today()

        await query.edit_message_text(
            format_milestone_history(
                today.year
            ),
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # -----------------------------------------------------
    # CANCEL MILESTONE
    # -----------------------------------------------------

    if callback_data == "panel:care:milestone:cancel":

        await query.edit_message_text(
            "❌ CANCEL MILESTONE\n\n"
            "First check the milestone ID using:\n"
            "/activemilestones\n\n"
            "Then send:\n"
            "/cancelmilestone ID confirm\n\n"
            "Example:\n"
            "/cancelmilestone 3 confirm",
            reply_markup=build_care_milestone_back_menu(),
        )

        return

    # =====================================================
    # CARE — ENCOURAGEMENT
    # =====================================================

    if callback_data.startswith(
        "panel:care:comingsoon:"
    ):

        await query.edit_message_text(
            "💌 ENCOURAGEMENT\n\n"
            "🚧 This CARE workflow has not been built yet.\n\n"
            "Completed:\n"
            "✅ Birthdays\n"
            "✅ Newcomers\n"
            "✅ Milestones\n\n"
            "Next:\n"
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