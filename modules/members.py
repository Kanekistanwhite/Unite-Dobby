from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from services.member_service import add_member, get_active_members
from services.permissions import is_approved_leader


async def add_member_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add a member using /addmember Name | DD-MM | leader."""

    if update.message is None:
        return

    user = update.effective_user

    if not is_approved_leader(
        user.id if user else None
    ):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
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

        birthday_day = int(day_text)
        birthday_month = int(month_text)

        member = add_member(
            display_name=display_name,
            birthday_day=birthday_day,
            birthday_month=birthday_month,
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


async def list_members_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """List all active members."""

    if update.message is None:
        return

    user = update.effective_user

    if not is_approved_leader(
        user.id if user else None
    ):
        await update.message.reply_text(
            "⛔ This command is only available to approved leaders."
        )
        return

    members = get_active_members()

    if not members:
        await update.message.reply_text(
            "There are no members in the database yet."
        )
        return

    member_lines = []

    for number, member in enumerate(
        members,
        start=1,
    ):
        birthday = (
            f"{member.birthday_day:02d}-"
            f"{member.birthday_month:02d}"
        )

        leader_label = (
            " 👑"
            if member.is_leader
            else ""
        )

        member_lines.append(
            f"{number}. {member.display_name}"
            f"{leader_label} — {birthday}"
        )

    await update.message.reply_text(
        "👥 Unite Dobby Members\n\n"
        + "\n".join(member_lines)
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
            "listmembers",
            list_members_command,
        )
    )