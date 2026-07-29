from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def chat_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the Telegram ID of the current chat."""
    chat = update.effective_chat

    if chat is None or update.message is None:
        return

    await update.message.reply_text(
        f"Chat name: {chat.title or 'Private chat'}\n"
        f"Chat ID: {chat.id}\n"
        f"Chat type: {chat.type}"
    )


def register_admin_handlers(application: Application) -> None:
    """Register admin-related commands."""
    application.add_handler(CommandHandler("chatid", chat_id))