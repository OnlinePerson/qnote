import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from database.db import init_db, seed_shop
from bot.handlers import start, farm, group

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    logger.info("در حال راه‌اندازی دیتابیس...")
    init_db()
    seed_shop()
    logger.info("ربات ZooBoom آماده شد! 🚀")


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN تنظیم نشده است!")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ثبت روترها
    dp.include_router(start.router)
    dp.include_router(farm.router)
    dp.include_router(group.router)

    # هوک استارتاپ
    dp.startup.register(on_startup)

    logger.info("شروع polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
