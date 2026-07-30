import logging

from telegram.ext import Application

from config.settings import BOT_TOKEN
from database.database import DATABASE_PATH, init_database
from modules.admin import register_admin_handlers
from modules.birthdays import register_birthday_handlers
from modules.biweekly import register_biweekly_handlers
from modules.members import register_member_handlers
from modules.start import register_start_handlers
from modules.sunday import register_sunday_handlers


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    """Start Unite Dobby."""

    logger.info("Initialising database at %s", DATABASE_PATH)
    init_database()
    logger.info("Database is ready.")

    application = Application.builder().token(BOT_TOKEN).build()

    register_start_handlers(application)
    register_admin_handlers(application)
    register_sunday_handlers(application)
    register_biweekly_handlers(application)
    register_member_handlers(application)
    register_birthday_handlers(application)

    logger.info("Unite Dobby is running...")

    application.run_polling(
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()