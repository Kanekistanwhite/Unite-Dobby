from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from services.member_service import (
    add_member,
    get_active_members_with_planners,
    set_birthday_planner,
)
from services.permissions import is_approved_leader


async def check_leader_permission(
    update: Update,
) -> bool:
    """Check whether the user may use member-management commands."""

    if update.message is None:
        return False

    user = update.effective_user

    if not is_approved_leader(
        user.id if user else None
    ):
        await update.message.reply_text(
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

    if update.message is None:
        return

    command_text = update.message.text or ""

    try:
        details = command_text.split(
            " ",
            maxsplit=1,
        )[1]
    except IndexError:
        await update.message.reply_text(
            "Usage:\n"
            "/addmember Name | DD-MM\n\n"
            "For a leader:\n"
            "/addmember Name | DD-MM | leader"
        )
        return

    parts = [
        part.strip()
        for part in details.split("|")
    ]

    if len(parts) not in (2, 3):
        await update.message.reply_text(
            "Please use this format:\n"
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
        day_text, month_text = birthday_text.split("-")

        member = add_member(
            display_name=display_name,
            birthday_day=int(day_text),
            birthday_month=int(month_text),
            is_leader=is_leader,
        )

    except ValueError as error:
        await update.message.reply_text(
            f"❌ {error}"
        )
        return

    leader_label = (
        "\n👑 Leader"
        if member.is_leader
        else ""
    )

    await update.message.reply_text(
        "✅ Member added\n\n"
        f"Name: {member.display_name}\n"
        f"Birthday: "
        f"{member.birthday_day:02d}-"
        f"{member.birthday_month:02d}"
        f"{leader_label}"
    )


async def set_planner_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Assign a birthday planner using /setplanner Member | Planner."""

    if not await check_leader_permission(update):
        return

    if update.message is None:
        return

    command_text = update.message.text or ""

    try:
        details = command_text.split(
            " ",
            maxsplit=1,
        )[1]
    except IndexError:
        await update.message.reply_text(
            "Usage:\n"
            "/setplanner Member | Planner\n\n"
            "Example:\n"
            "/setplanner Charlotte | Gordon"
        )
        return

    parts = [
        part.strip()
        for part in details.split("|")
    ]

    if len(parts) != 2:
        await update.message.reply_text(
            "Please use this format:\n"
            "/setplanner Member | Planner"
        )
        return

    try:
        member, planner = set_birthday_planner(
            member_name=parts[0],
            planner_name=parts[1],
        )
    except ValueError as error:
        await update.message.reply_text(
            f"❌ {error}"
        )
        return

    await update.message.reply_text(
        "✅ Birthday planner assigned\n\n"
        f"Member: {member.display_name}\n"
        f"Planner: {planner.display_name}"
    )


async def list_members_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """List active members and their birthday planners."""

    if not await check_leader_permission(update):
        return

    if update.message is None:
        return

    members = get_active_members_with_planners()

    if not members:
        await update.message.reply_text(
            "There are no members in the database yet."
        )
        return

    member_lines = []

    for number, (member, planner_name) in enumerate(
        members,
        start=1,
    ):
        if (
            member.birthday_day is not None
            and member.birthday_month is not None
        ):
            birthday = (
                f"{member.birthday_day:02d}-"
                f"{member.birthday_month:02d}"
            )
        else:
            birthday = "Not set"

        leader_label = (
            " 👑"
            if member.is_leader
            else ""
        )

        planner = planner_name or "Not assigned"

        member_lines.append(
            f"{number}. {member.display_name}"
            f"{leader_label} — {birthday}\n"
            f"   🎁 Planner: {planner}"
        )

    await update.message.reply_text(
        "👥 Unite Dobby Members\n\n"
        + "\n\n".join(member_lines)
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
            "listmembers",
            list_members_command,
        )
    )