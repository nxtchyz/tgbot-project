import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, Message, CallbackQuery

import config
from db import crud
from db.models import init_db
from bot.handlers import planner, start, schedule, ai_chat
from bot.handlers.start import MAIN_MENU_COMMANDS
from bot.scheduler import setup_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def save_user_middleware(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    user = None
    if isinstance(event, Message):
        user = event.from_user
    elif isinstance(event, CallbackQuery):
        user = event.from_user
    if user:
        await crud.upsert_user(user.id, user.username, user.first_name)
    return await handler(event, data)


async def main() -> None:
    await init_db()
    log.info("Database initialized")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(save_user_middleware)
    dp.callback_query.middleware(save_user_middleware)

    dp.include_router(start.router)
    dp.include_router(planner.router)
    dp.include_router(schedule.router)
    dp.include_router(ai_chat.router)  # последним — ловит всё остальное

    await bot.set_my_commands(MAIN_MENU_COMMANDS)
    log.info("Bot commands set")

    setup_scheduler(bot)
    log.info("Scheduler started")

    log.info("Bot is starting...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
