from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


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


def register_sunday_handlers(application: Application) -> None:
    """Register Sunday attendance commands."""
    application.add_handler(CommandHandler("testsunday", test_sunday))