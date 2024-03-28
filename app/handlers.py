import json

from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.utils import initialize, generate_json, date_to_obj, date_from_obj

router = Router()

with open('config.json', 'r') as config_json:
    config = json.load(config_json)


class Reg(StatesGroup):
    increase_value_week_1 = State()
    increase_value_week_2 = State()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(f'{message.from_user.first_name} Добро пожаловать', reply_markup=kb.main)


@router.message(F.text == "Запросить отчет")
async def send_report(message: Message):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    await message.answer(f"Текущая отчетная неделя\nДата: {date_from_obj} - {date_to_obj}\n"
                         f"Увелечение на первой неделе: {config['increase_percent_week_1']}%\n"
                         f"Увелечение на второй неделе: {config['increase_percent_week_2']}%",
                         reply_markup=kb.report_settings)


@router.message(F.text == "Запросить заказ")
async def send_order(message: Message):
    await message.answer("Функция в разработке...")


@router.callback_query(F.data == "generate_report")
async def increase_value_w1_callback(callback: CallbackQuery):
    await callback.answer()
    await generate_json()
    await initialize()
    await callback.message.answer_document(
        document=types.FSInputFile(
            path="data.xlsx"
        )
    )


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery):
    await callback.answer()
    await send_report()


@router.callback_query(F.data == "increase_w1")
async def increase_value_w1_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите увелечение в %')
    await state.set_state(Reg.increase_value_week_1)


@router.callback_query(F.data == "increase_w2")
async def increase_value_w2_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите увелечение в %')
    await state.set_state(Reg.increase_value_week_2)


@router.callback_query(F.data == "shipment_w1")
async def add_shipment_w1_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    pass


@router.callback_query(F.data == "shipment_w2")
async def add_shipment_w2_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    pass


@router.message(Reg.increase_value_week_1)
async def increase_value_w1_handler(message: Message, state: FSMContext):
    try:
        increase_percent = int(message.text)
        if 0 <= increase_percent <= 100:
            increase_value = (float(increase_percent) / 100) + 1
            config['increase_value_week_1'] = increase_value
            config['increase_percent_week_1'] = increase_percent
            with open('config.json', 'w') as config_json:
                json.dump(config, config_json, indent=4)
            await message.answer(f'Увелечение на первой неделе {increase_percent}%', reply_markup=kb.main)
            await state.clear()
        else:
            await message.answer('Ведите число от 0 до 100')
    except ValueError:
        await message.answer('Введите целое число')


@router.message(Reg.increase_value_week_2)
async def increase_value_w2_handler(message: Message, state: FSMContext):
    try:
        increase_percent = int(message.text)
        if 0 <= increase_percent <= 100:
            increase_value = (float(increase_percent) / 100) + 1
            config['increase_value_week_2'] = increase_value
            config['increase_percent_week_2'] = increase_percent
            with open('config.json', 'w') as config_json:
                json.dump(config, config_json, indent=4)
            await message.answer(f'Увелечение на второй неделе {increase_percent}%', reply_markup=kb.main)
            await state.clear()
        else:
            await message.answer('Ведите число от 0 до 100')
    except ValueError:
        await message.answer('Введите целое число')
