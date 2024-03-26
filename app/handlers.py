from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command

import app.keyboards as kb
from app.utils import initialize, generate_json

router = Router()


@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer(f'{message.from_user.first_name} Добро пожаловать', reply_markup=kb.main)


@router.message(F.text == "Запросить отчет")
async def send_report(message: types.Message):
    await initialize()
    await message.reply_document(
        document=types.FSInputFile(
            path="data.xlsx"
        )
    )


@router.message(F.text == "Запросить заказ")
async def send_order(message: types.Message):
    await message.answer("Функция в разработке...")
