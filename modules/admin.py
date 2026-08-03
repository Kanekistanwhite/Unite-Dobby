from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


async def chat_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the Telegram ID of the current chat."""

    chat = update.effective_chat
    message = update.effective_message

    if chat is None or message is None:
        return

    await message.reply_text(
        f"💬 Chat details\n\n"
        f"Chat name: {chat.title or 'Private chat'}\n"
        f"Chat ID: {chat.id}\n"
        f"Chat type: {chat.type}\n"
        f"Forum topics enabled: {'Yes' if chat.is_forum else 'No'}"
    )


async def topic_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the current chat ID and forum-topic ID."""

    chat = update.effective_chat
    message = update.effective_message

    if chat is None or message is None:
        return

    thread_id = message.message_thread_id

    if thread_id is None:
        await message.reply_text(
            "🧵 Topic details\n\n"
            f"Chat name: {chat.title or 'Private chat'}\n"
            f"Chat ID: {chat.id}\n"
            "Topic ID: Not detected\n\n"
            "Send /topicid from inside the specific "
            "Telegram topic you want Dobby to use."
        )
        return

    await message.reply_text(
        "🧵 Topic details\n\n"
        f"Chat name: {chat.title or 'Unknown chat'}\n"
        f"Chat ID: {chat.id}\n"
        f"Topic ID: {thread_id}"
    )


async def my_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the Telegram ID of the person using the command."""

    user = update.effective_user
    message = update.effective_message

    if user is None or message is None:
        return

    username = (
        f"@{user.username}"
        if user.username
        else "No username"
    )

    await message.reply_text(
        "👤 Your Telegram details\n\n"
        f"Name: {user.full_name}\n"
        f"Username: {username}\n"
        f"User ID: {user.id}"
    )


def register_admin_handlers(
    application: Application,
) -> None:
    """Register admin-related commands."""

    application.add_handler(
        CommandHandler(
            "chatid",
            chat_id,
        )
    )

    application.add_handler(
        CommandHandler(
            "topicid",
            topic_id,
        )
    )

    application.add_handler(
        CommandHandler(
            "myid",
            my_id,
        )
    )