import logging
from calendar import month_abbr

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from services.birthday_service import seed_birthday_roster
from services.member_service import (
    add_member,
    deactivate_member,
    get_active_members_with_planners,
    set_birthday_planner,
)
from services.permissions import is_approved_leader


logger = logging.getLogger(__name__)


async def check_leader_permission(
    update: Update,
) -> bool:
    """Check whether the user may use member-management commands."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return False

    user_id = user.id if user else None

    if not is_approved_leader(user_id):
        await message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return False

    return True


async def add_member_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add a member using /addmember Name | DD-MM | leader."""

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    command_text = message.text or ""

    try:
        details = command_text.split(
            " ",
            maxsplit=1,
        )[1]
    except IndexError:
        await message.reply_text(
            "Usage:\n"
            "/addmember Name | DD-MM\n\n"
            "For a leader:\n"
            "/addmember Name | DD-MM | leader\n\n"
            "Example:\n"
            "/addmember Kelly | 09-01"
        )
        return

    parts = [
        part.strip()
        for part in details.split("|")
    ]

    if len(parts) not in (2, 3):
        await message.reply_text(
            "Please use this format:\n"
            "/addmember Name | DD-MM\n\n"
            "For a leader:\n"
            "/addmember Name | DD-MM | leader"
        )
        return

    display_name = parts[0]
    birthday_text = parts[1]

    is_leader = (
        len(parts) == 3
        and parts[2].lower() == "leader"
    )

    try:
        day_text, month_text = birthday_text.split(
            "-",
            maxsplit=1,
        )

        member = add_member(
            display_name=display_name,
            birthday_day=int(day_text),
            birthday_month=int(month_text),
            is_leader=is_leader,
        )

    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    leader_text = (
        "Yes"
        if member.is_leader
        else "No"
    )

    birthday_month_name = month_abbr[
        member.birthday_month
    ].upper()

    await message.reply_text(
        "✅ Member added\n\n"
        f"👤 Name: {member.display_name}\n"
        f"🎂 Birthday: "
        f"{member.birthday_day} "
        f"{birthday_month_name}\n"
        f"👑 Leader: {leader_text}"
    )


async def set_planner_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Assign a birthday planner to a member."""

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    command_text = message.text or ""

    try:
        details = command_text.split(
            " ",
            maxsplit=1,
        )[1]
    except IndexError:
        await message.reply_text(
            "Usage:\n"
            "/setplanner Member Name | Planner Name\n\n"
            "Example:\n"
            "/setplanner Kelly | Gordon"
        )
        return

    parts = [
        part.strip()
        for part in details.split("|")
    ]

    if len(parts) != 2:
        await message.reply_text(
            "Please use this format:\n"
            "/setplanner Member Name | Planner Name"
        )
        return

    member_name = parts[0]
    planner_name = parts[1]

    try:
        member, planner = set_birthday_planner(
            member_name,
            planner_name,
        )
    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    await message.reply_text(
        "✅ Birthday planner assigned\n\n"
        f"👤 Member: {member.display_name}\n"
        f"🎁 Planner: {planner.display_name}"
    )


async def remove_member_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Deactivate a member after an explicit confirmation."""

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    if len(context.args) < 2:
        await message.reply_text(
            "Usage:\n"
            "/removemember Member Name confirm\n\n"
            "Example:\n"
            "/removemember Declan confirm"
        )
        return

    confirmation = context.args[-1].strip().lower()

    if confirmation != "confirm":
        await message.reply_text(
            "❌ Removal was not confirmed.\n\n"
            "Add the word 'confirm' after the member's name.\n\n"
            "Example:\n"
            "/removemember Declan confirm"
        )
        return

    member_name = " ".join(
        context.args[:-1]
    ).strip()

    try:
        member = deactivate_member(
            member_name
        )
    except ValueError as error:
        await message.reply_text(
            f"❌ {error}"
        )
        return

    await message.reply_text(
        "✅ Member removed from the active roster\n\n"
        f"👤 Name: {member.display_name}\n\n"
        "They will no longer appear in the member list, "
        "birthday checks or birthday-planning reminders."
    )


async def list_members_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """List active members in birthday order."""

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    members = get_active_members_with_planners()

    if not members:
        await message.reply_text(
            "There are no members in the database yet."
        )
        return

    # Sort members from January to December.
    # Within each month, members are sorted by birthday day.
    # Members without a birthday appear at the bottom.
    members.sort(
        key=lambda item: (
            item[0].birthday_month
            if item[0].birthday_month is not None
            else 13,
            item[0].birthday_day
            if item[0].birthday_day is not None
            else 32,
            item[0].display_name.lower(),
        )
    )

    member_sections: list[str] = []

    for number, (member, planner_name) in enumerate(
        members,
        start=1,
    ):
        if (
            member.birthday_day is not None
            and member.birthday_month is not None
            and 1 <= member.birthday_month <= 12
        ):
            birthday_month_name = month_abbr[
                member.birthday_month
            ].upper()

            birthday = (
                f"{member.birthday_day} "
                f"{birthday_month_name}"
            )
        else:
            birthday = "Not set"

        leader_label = (
            " 👑"
            if member.is_leader
            else ""
        )

        planner = planner_name or "Not assigned"

        member_sections.append(
            f"{number}. {member.display_name}{leader_label}\n"
            f"   🎂 {birthday}\n"
            f"   🎁 Planner: {planner}"
        )

    await message.reply_text(
        "👥 UNITE MEMBERS — BIRTHDAY ORDER\n\n"
        + "\n\n".join(member_sections)
    )


async def setup_birthdays_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Import or update the complete birthday roster."""

    if not await check_leader_permission(update):
        return

    message = update.effective_message

    if message is None:
        return

    await message.reply_text(
        "⏳ Updating the birthday roster..."
    )

    try:
        created, updated, planners = seed_birthday_roster()

    except Exception:
        logger.exception(
            "The birthday roster could not be updated."
        )

        await message.reply_text(
            "❌ The birthday roster could not be updated.\n\n"
            "Check the Railway logs for details."
        )
        return

    await message.reply_text(
        "✅ Birthday roster updated\n\n"
        f"New members added: {created}\n"
        f"Existing members updated: {updated}\n"
        f"Planner assignments updated: {planners}"
    )


def register_member_handlers(
    application: Application,
) -> None:
    """Register member-management commands."""

    application.add_handler(
        CommandHandler(
            "addmember",
            add_member_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "setplanner",
            set_planner_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "removemember",
            remove_member_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "listmembers",
            list_members_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "setupbirthdays",
            setup_birthdays_command,
        )
    )