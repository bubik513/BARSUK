import asyncio
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Dict, Any, Awaitable, Callable
from aiogram.types import Update

from app import setup_handlers
from app.utils.database import init_db, async_session
from config import Config


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            data["db"] = session
            return await handler(event, data)


async def main():
    print("Инициализация базы данных...")
    await init_db()

    storage = MemoryStorage()

    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DatabaseMiddleware(async_session))

    setup_handlers(dp)

    print("Бот запущен! Используйте Ctrl+C для остановки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())