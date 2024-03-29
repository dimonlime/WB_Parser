from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Запросить отчет')],
    [KeyboardButton(text='Запросить заказ')]
], resize_keyboard=True, input_field_placeholder='Выберите действие...')

report_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить увелечение на 1-ую неделю", callback_data='increase_w1')],
    [InlineKeyboardButton(text="Добавить увелечение на 2-ую неделю", callback_data='increase_w2')],
    [InlineKeyboardButton(text="Добавить поставки", callback_data='shipment')],
    [InlineKeyboardButton(text="Запросить отчет", callback_data='generate_report')]
])


async def inline_incomes():
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    keyboard = InlineKeyboardBuilder()
    for article_key in config['Article']:
        keyboard.add(InlineKeyboardButton(text=article_key, callback_data=f'article_{article_key}'))
    return keyboard.adjust(1).as_markup()
