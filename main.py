"""Точка входа: инициализация бота, регистрация роутеров, запуск polling."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.crud import init_db
from handlers.admin.admin_menu import router as admin_menu_router
from handlers.admin.coefficients import router as coeffs_router
from handlers.admin.prices import router as prices_router
from handlers.user.calculator import router as calc_router
from handlers.user.confirm import router as confirm_router
from handlers.user.start import router as start_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


async def main() -> None:
    """Запуск бота."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан в .env")

    # Инициализация базы данных
    await init_db()
    log.info("Database initialized")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок регистрации важен: более специфичные роутеры — первыми
    dp.include_router(start_router)
    dp.include_router(admin_menu_router)
    dp.include_router(prices_router)
    dp.include_router(coeffs_router)
    dp.include_router(calc_router)
    dp.include_router(confirm_router)

    log.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
