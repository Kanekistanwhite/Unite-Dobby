from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from services.permissions import is_approved_leader


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Introduce Unite Dobby and show the leader menu button."""

    message = update.effective_message
    user = update.effective_user

    if message is None:
        return

    first_name = (
        user.first_name
        if user is not None
        else "there"
    )

    user_id = (
        user.id
        if user is not None
        else None
    )

    if is_approved_leader(user_id):
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🧰 Open Dobby Control Panel",
                        callback_data="panel:open",
                    )
                ]
            ]
        )

        await message.reply_text(
            f"Hello {first_name} 👋\n\n"
            "I am Unite Dobby, your UNITE assistant.\n\n"
            "I help with:\n"
            "⛪ Sunday attendance\n"
            "🏠 Bi-weekly attendance\n"
            "🎂 Birthday greetings\n"
            "🎁 Birthday planning reminders\n\n"
            "Use the button below instead of remembering "
            "every command.",
            reply_markup=keyboard,
        )
        return

    await message.reply_text(
        f"Hello {first_name} 👋\n\n"
        "I am Unite Dobby, your UNITE assistant."
    )


def register_start_handlers(
    application: Application,
) -> None:
    """Register commands belonging to the start module."""

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )