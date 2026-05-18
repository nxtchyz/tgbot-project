import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from db.models import init_db
from bot.handlers import planner, start, schedule
from bot.handlers.start import MAIN_MENU_COMMANDS
from bot.scheduler import setup_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    await init_db()
    log.info("Database initialized")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(planner.router)
    dp.include_router(schedule.router)

    await bot.set_my_commands(MAIN_MENU_COMMANDS)
    log.info("Bot commands set")

    setup_scheduler(bot)
    log.info("Scheduler started")

    log.info("Bot is starting...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
