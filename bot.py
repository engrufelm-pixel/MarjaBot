import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db, async_session
from handlers import start, calculator, products, ai_content, settings
from middlewares.db import DbSessionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан. Создай файл .env и добавь BOT_TOKEN.")
        return

    logger.info("Инициализация базы данных...")
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware: инъекция сессии БД в каждый хендлер
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))

    # Регистрация роутеров (порядок важен: start первый, чтобы main_menu callback был приоритетным)
    dp.include_router(start.router)
    dp.include_router(calculator.router)
    dp.include_router(products.router)
    dp.include_router(ai_content.router)
    dp.include_router(settings.router)

    logger.info("Бот запускается...")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
