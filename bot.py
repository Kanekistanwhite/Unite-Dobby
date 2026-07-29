import logging

from telegram.ext import Application

from config.settings import BOT_TOKEN
from database.database import DATABASE_PATH, init_database
from modules.admin import register_admin_handlers
from modules.biweekly import register_biweekly_handlers
from modules.start import register_start_handlers
from modules.sunday import register_sunday_handlers


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Start Unite Dobby."""

    # Create or check the database before Telegram starts
    logger.info("Initialising database at %s", DATABASE_PATH)
    init_database()
    logger.info("Database is ready.")

    # Start the Telegram application
    application = Application.builder().token(BOT_TOKEN).build()

    register_start_handlers(application)
    register_admin_handlers(application)
    register_sunday_handlers(application)
    register_biweekly_handlers(application)

    logger.info("Unite Dobby is running...")

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()