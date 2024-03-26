import asyncio
import logging
import os
import sys
import dotenv
from aiogram import Dispatcher, Bot
from app.handlers import router

dp = Dispatcher()


async def main():
    dp.include_router(router)
    dotenv.load_dotenv()
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
