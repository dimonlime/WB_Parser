from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Запросить отчет')],
    [KeyboardButton(text='Запросить заказ')],
    [KeyboardButton(text='Обновить артикулы поставок')]
], resize_keyboard=True, input_field_placeholder='Выберите действие...')

update_article_income = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Обновить", callback_data='get_update_income'),
     InlineKeyboardButton(text="Отмена", callback_data='cancel_update_income')]
])

report_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить увелечение на 1-ой недели", callback_data='increase_w1')],
    [InlineKeyboardButton(text="Добавить увелечение на 2-ой недели", callback_data='increase_w2')],
    [InlineKeyboardButton(text="Добавить поставки на 1-ой неделе", callback_data='shipment_w1')],
    [InlineKeyboardButton(text="Добавить поставки на 2-ой неделе", callback_data='shipment_w2')],
    [InlineKeyboardButton(text="Запросить отчет", callback_data='generate_report')]
])


async def inline_incomes_week_1():
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    keyboard = InlineKeyboardBuilder()
    for article_key in config['Article_week_1']:
        keyboard.add(InlineKeyboardButton(text=article_key, callback_data=f'article_week_1{article_key}'))
    return keyboard.adjust(1).as_markup()


async def inline_incomes_week_2():
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    keyboard = InlineKeyboardBuilder()
    for article_key in config['Article_week_2']:
        keyboard.add(InlineKeyboardButton(text=article_key, callback_data=f'article_week_2{article_key}'))
    return keyboard.adjust(1).as_markup()
