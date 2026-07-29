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


async def my_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the Telegram ID of the person using the command."""
    user = update.effective_user

    if user is None or update.message is None:
        return

    username = (
        f"@{user.username}"
        if user.username
        else "No username"
    )

    await update.message.reply_text(
        "👤 Your Telegram details\n\n"
        f"Name: {user.full_name}\n"
        f"Username: {username}\n"
        f"User ID: {user.id}"
    )


def register_admin_handlers(application: Application) -> None:
    """Register admin-related commands."""
    application.add_handler(
        CommandHandler("chatid", chat_id)
    )

    application.add_handler(
        CommandHandler("myid", my_id)
    )