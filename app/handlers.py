import json

import aiogram.utils.magic_filter
from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.utils import initialize, generate_json, date_to_obj, date_from_obj, update_incomes

router = Router()


class Reg(StatesGroup):
    increase_value_week_1 = State()
    increase_value_week_2 = State()
    increase_incomes_w1 = State()
    increase_incomes_w2 = State()
    update_articles = State()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(f'{message.from_user.first_name} Добро пожаловать', reply_markup=kb.main)


@router.message(F.text == "Запросить отчет")
async def send_report(message: Message):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    await message.answer(f"Текущая отчетная неделя:\nДата: {date_from_obj} - {date_to_obj}\n"
                         f"Увелечение на первой неделе: {config['Settings']['increase_percent_week_1']}%\n"
                         f"Увелечение на второй неделе: {config['Settings']['increase_percent_week_2']}%",
                         reply_markup=kb.report_settings)


@router.message(F.text == "Обновить артикулы поставок")
async def send_report(message: Message, state: FSMContext):
    await state.set_state(Reg.update_articles)
    await message.answer(f"Внимание! Предыдущие значения поставок будут удалены, продолжить?",
                         reply_markup=kb.update_article_income)


@router.callback_query(F.data == "cancel_update_income")
async def cancel_update_income(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Действие отменено", reply_markup=kb.main)
    await state.clear()


@router.message(F.text == "Запросить заказ")
async def send_order(message: Message):
    await message.answer("Функция в разработке...")


@router.callback_query(F.data == "get_update_income")
async def get_update_incomes(callback: CallbackQuery):
    await callback.answer()
    await update_incomes()
    await callback.message.answer("Список артикулов успешно обновлен")


@router.callback_query(F.data == "generate_report")
async def generate_report(callback: CallbackQuery):
    await callback.answer('Запрос обрабатывается')
    await generate_json()
    await initialize()
    await callback.message.answer_document(
        document=types.FSInputFile(
            path="data.xlsx"
        )
    )


@router.callback_query(F.data == "increase_w1")
async def increase_value_w1_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите увелечение в %')
    await state.set_state(Reg.increase_value_week_1)


@router.callback_query(F.data == "increase_w2")
async def increase_value_w2_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.increase_value_week_2)
    await callback.answer()
    await callback.message.answer('Введите увелечение в %')


@router.callback_query(F.data == "shipment_w1")
async def add_shipment_w1_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Выберите артикул для изменения поставок:',
                                  reply_markup=await kb.inline_incomes_week_1())


@router.callback_query(F.data == "shipment_w2")
async def add_shipment_w1_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Выберите артикул для изменения поставок:',
                                  reply_markup=await kb.inline_incomes_week_2())


@router.callback_query(F.data.startswith('article_week_1'))
async def increse_incomes_w1_callback(callback: CallbackQuery, state: FSMContext):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    await state.set_state(Reg.increase_incomes_w1)
    await callback.answer()
    article_name = str(callback.data)
    await state.update_data(article_name=article_name[14:])
    await callback.message.answer(f'Артикул {article_name[14:]}\n'
                                  f'Текущее значение {config['Article_week_1'][article_name[14:]]['quantity']}\n'
                                  f'Введите новое значение:')


@router.callback_query(F.data.startswith('article_week_2'))
async def increse_incomes_w2_callback(callback: CallbackQuery, state: FSMContext):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    await state.set_state(Reg.increase_incomes_w2)
    await callback.answer()
    article_name = str(callback.data)
    await state.update_data(article_name=article_name[14:])
    await callback.message.answer(f'Артикул {article_name[14:]}\n'
                                  f'Текущее значение {config['Article_week_2'][article_name[14:]]['quantity']}\n'
                                  f'Введите новое значение:')


@router.message(Reg.increase_incomes_w1)
async def increase_incomes_w1(message: Message, state: FSMContext):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    try:
        increase_value = int(message.text)
        if 0 <= increase_value:
            data = await state.get_data()
            article_name = data['article_name']
            config['Article_week_1'][article_name]['quantity'] = increase_value
            with open('config.json', 'w') as config_json:
                json.dump(config, config_json, indent=4)
            await message.answer(f'Поставки {article_name} = {increase_value}', reply_markup=kb.main)
            await state.clear()
        else:
            await message.answer('Нельзя ввести число меньше нуля')
    except ValueError:
        await message.answer('Введите целое число')


@router.message(Reg.increase_incomes_w2)
async def increase_incomes_w1(message: Message, state: FSMContext):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    try:
        increase_value = int(message.text)
        if 0 <= increase_value:
            data = await state.get_data()
            article_name = data['article_name']
            config['Article_week_2'][article_name]['quantity'] = increase_value
            with open('config.json', 'w') as config_json:
                json.dump(config, config_json, indent=4)
            await message.answer(f'Поставки {article_name} = {increase_value}', reply_markup=kb.main)
            await state.clear()
        else:
            await message.answer('Нельзя ввести число меньше нуля')
    except ValueError:
        await message.answer('Введите целое число')


@router.message(Reg.increase_value_week_1)
async def increase_value_w1_handler(message: Message, state: FSMContext):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    try:
        increase_percent = int(message.text)
        if 0 <= increase_percent <= 100:
            increase_value = (float(increase_percent) / 100) + 1
            config['Settings']['increase_value_week_1'] = increase_value
            config['Settings']['increase_percent_week_1'] = increase_percent
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
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    try:
        increase_percent = int(message.text)
        if 0 <= increase_percent <= 100:
            increase_value = (float(increase_percent) / 100) + 1
            config['Settings']['increase_value_week_2'] = increase_value
            config['Settings']['increase_percent_week_2'] = increase_percent
            with open('config.json', 'w') as config_json:
                json.dump(config, config_json, indent=4)
            await message.answer(f'Увелечение на второй неделе {increase_percent}%', reply_markup=kb.main)
            await state.clear()
        else:
            await message.answer('Ведите число от 0 до 100')
    except ValueError:
        await message.answer('Введите целое число')
