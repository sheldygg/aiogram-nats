import asyncio

from aiogram import Bot, Dispatcher

from bot.config_reader import config
from bot.handlers import setup_routers


async def main() -> None:
    bot = Bot(config.bot_token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher()

    dp.include_router(setup_routers())
    await dp.start_polling(bot)



asyncio.run(main())
