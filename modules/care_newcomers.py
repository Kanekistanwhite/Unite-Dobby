from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config.settings import (
    CARE_LEADER_USER_IDS,
)
from services.care_newcomer_service import (
    add_newcomer_stock,
    find_newcomer,
    format_newcomer_inventory,
    format_newcomer_record,
    format_newcomer_register,
    get_singapore_today,
    give_pack_to_newcomer,
    register_newcomer,
    set_newcomer_stock,
)


# =========================================================
# PERMISSIONS
# =========================================================

def is_care_leader(
    user_id: int | None,
) -> bool:
    """Check whether user is an approved CARE leader."""

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
# ADD NEWCOMER
# =========================================================

async def add_newcomer_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Register a new CARE newcomer."""

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

    newcomer_name = (
        newcomer_name.strip()
    )

    invited_by = (
        invited_by.strip()
    )

    if (
        not newcomer_name
        or not invited_by
    ):

        await message.reply_text(
            "❌ Please include both the newcomer's "
            "name and who invited them.\n\n"
            "Example:\n"
            "/addnewcomer John Tan | Gordon"
        )

        return

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

    # -----------------------------------------------------
    # DUPLICATE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SUCCESS — PACK GIVEN
    # -----------------------------------------------------

    if status == "registered":

        response = (
            "✅ NEWCOMER REGISTERED\n\n"
            f"👋 Name: {newcomer.display_name}\n"
            f"🙋 Invited by: {newcomer.invited_by}\n"
            f"📅 First visit: "
            f"{newcomer.first_visit_date.strftime('%d %b %Y')}\n"
            "🎁 Newcomer pack: ✅ Given\n\n"
            f"📦 Packs remaining: {inventory.current_stock}\n\n"
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
                "\n\n"
                "⚠️ LOW STOCK WARNING\n"
                f"Only {inventory.current_stock} "
                "newcomer pack(s) remain."
            )

        await message.reply_text(
            response
        )

        return

    # -----------------------------------------------------
    # SUCCESS — NO PACK AVAILABLE
    # -----------------------------------------------------

    await message.reply_text(
        "✅ NEWCOMER REGISTERED\n\n"
        f"👋 Name: {newcomer.display_name}\n"
        f"🙋 Invited by: {newcomer.invited_by}\n"
        f"📅 First visit: "
        f"{newcomer.first_visit_date.strftime('%d %b %Y')}\n"
        "🎁 Newcomer pack: ❌ NOT GIVEN\n\n"
        "🚨 There are currently no newcomer packs left.\n\n"
        "After replenishing stock, use:\n"
        f"/givepack {newcomer.display_name}\n\n"
        "📝 REMINDER:\n"
        f"Please remember to add "
        f"{newcomer.display_name} into the "
        "CARE Newcomer Master Sheet."
    )


# =========================================================
# FIND NEWCOMER
# =========================================================

async def find_newcomer_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Search the newcomer register."""

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
            "/findnewcomer NAME\n\n"
            "Example:\n"
            "/findnewcomer John Tan"
        )

        return

    newcomer = find_newcomer(
        name
    )

    if newcomer is None:

        await message.reply_text(
            "🔎 NEWCOMER NOT FOUND\n\n"
            f"No record was found for:\n{name}"
        )

        return

    await message.reply_text(
        "🔎 NEWCOMER FOUND\n\n"
        f"{format_newcomer_record(newcomer)}"
    )


# =========================================================
# REGISTER
# =========================================================

async def newcomer_register_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show recent newcomer register."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        format_newcomer_register()
    )


# =========================================================
# INVENTORY
# =========================================================

async def newcomer_stock_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show newcomer-pack stock."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    year = (
        get_singapore_today().year
    )

    if context.args:

        try:

            year = int(
                context.args[0]
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid year."
            )

            return

    await message.reply_text(
        format_newcomer_inventory(
            year
        )
    )


# =========================================================
# SET PHYSICAL STOCK
# =========================================================

async def set_newcomer_stock_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Set the current physical stock count."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if not context.args:

        await message.reply_text(
            "Usage:\n"
            "/setnewcomerstock QUANTITY [YEAR]\n\n"
            "Example:\n"
            "/setnewcomerstock 34"
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

    except ValueError:

        await message.reply_text(
            "❌ Please enter a valid stock quantity and year."
        )

        return

    await message.reply_text(
        "✅ NEWCOMER STOCK UPDATED\n\n"
        f"Year: {year}\n"
        f"Current physical stock: "
        f"{inventory.current_stock}"
    )


# =========================================================
# ADD REPLENISHED STOCK
# =========================================================

async def add_newcomer_stock_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add newly prepared newcomer packs."""

    if not await check_care_permission(
        update
    ):
        return

    message = update.effective_message

    if message is None:
        return

    if not context.args:

        await message.reply_text(
            "Usage:\n"
            "/addnewcomerstock QUANTITY [YEAR]\n\n"
            "Example:\n"
            "/addnewcomerstock 20"
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
        f"Current stock: {inventory.current_stock}"
    )


# =========================================================
# GIVE PACK LATER
# =========================================================

async def give_pack_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Mark an outstanding newcomer pack as given."""

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
            "/givepack NAME"
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
            "⚠️ PACK ALREADY GIVEN\n\n"
            f"{newcomer.display_name} has already "
            "received a newcomer pack."
        )

        return

    if status == "no_stock":

        await message.reply_text(
            "🚨 NO NEWCOMER PACKS AVAILABLE\n\n"
            "Please replenish the inventory first."
        )

        return

    await message.reply_text(
        "✅ NEWCOMER PACK GIVEN\n\n"
        f"👋 {newcomer.display_name}\n"
        "🎁 Pack: Given\n"
        f"📦 Packs remaining: {inventory.current_stock}"
    )


# =========================================================
# REGISTER HANDLERS
# =========================================================

def register_care_newcomer_handlers(
    application: Application,
) -> None:
    """Register CARE Newcomer commands."""

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