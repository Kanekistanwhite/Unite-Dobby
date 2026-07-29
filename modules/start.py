from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Respond when someone sends /start."""
    user = update.effective_user
    first_name = user.first_name if user else "there"

    if update.message is None:
        return

    await update.message.reply_text(
        f"Hello {first_name} 👋\n\n"
        "I am Unite Dobby, your life group assistant.\n\n"
        "I help with:\n"
        "⛪ Sunday attendance\n"
        "🍽️ Bi-weekly attendance\n"
        "🎂 Birthday greetings"
    )


def register_start_handlers(application: Application) -> None:
    """Register commands belonging to the start module."""
    application.add_handler(CommandHandler("start", start))