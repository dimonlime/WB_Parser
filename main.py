import asyncio
import logging
import os
import sys
import dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(f'{message.from_user.first_name} Добро пожаловать')


@dp.message()
async def answer(message: types.Message):
    await message.reply('bimba')


async def main():
    dotenv.load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
