from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


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


def register_biweekly_handlers(application: Application) -> None:
    """Register bi-weekly attendance commands."""
    application.add_handler(
        CommandHandler("testbiweekly", test_biweekly)
    )