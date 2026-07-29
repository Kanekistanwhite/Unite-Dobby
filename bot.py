import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# Load secret settings from the .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


# Display useful information in the terminal
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Respond when someone sends /start."""
    user = update.effective_user
    first_name = user.first_name if user else "there"

    await update.message.reply_text(
        f"Hello {first_name} 👋\n\n"
        "I am Unite Dobby, your life group assistant.\n\n"
        "I help with:\n"
        "⛪ Sunday attendance\n"
        "🍽️ Bi-weekly attendance\n"
        "🎂 Birthday greetings"
    )


async def chat_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the Telegram ID of the current chat."""
    chat = update.effective_chat

    if chat is None:
        return

    await update.message.reply_text(
        f"Chat name: {chat.title or 'Private chat'}\n"
        f"Chat ID: {chat.id}\n"
        f"Chat type: {chat.type}"
    )


async def test_sunday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Create a test Sunday attendance poll."""
    chat = update.effective_chat

    if chat is None:
        return

    await context.bot.send_message(
        chat_id=chat.id,
        text=(
            "⛪ Sunday Attendance\n\n"
            "Select everything you can attend.\n"
            "Choose CMI All only if you cannot make it for anything."
        ),
    )

    await context.bot.send_poll(
        chat_id=chat.id,
        question="Attendance for this Sunday",
        options=[
            "Morning Service",
            "Lunch",
            "Youth Service",
            "Hangout Afterwards",
            "CMI All",
        ],
        is_anonymous=False,
        allows_multiple_answers=True,
    )


async def test_biweekly(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Create a test bi-weekly attendance poll."""
    chat = update.effective_chat

    if chat is None:
        return

    await context.bot.send_message(
        chat_id=chat.id,
        text=(
            "🍽️ Bi-weekly Attendance\n\n"
            "Select every timing you can attend.\n"
            "Choose CMI Both only if you cannot attend either timing."
        ),
    )

    await context.bot.send_poll(
        chat_id=chat.id,
        question="Which timing can you make?",
        options=[
            "Lunch",
            "Dinner",
            "CMI Both",
        ],
        is_anonymous=False,
        allows_multiple_answers=True,
    )


def main() -> None:
    """Start Unite Dobby."""
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Check that your .env file exists "
            "and contains BOT_TOKEN=your_token."
        )

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chatid", chat_id))
    application.add_handler(CommandHandler("testsunday", test_sunday))
    application.add_handler(CommandHandler("testbiweekly", test_biweekly))

    logger.info("Unite Dobby is running...")

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
    