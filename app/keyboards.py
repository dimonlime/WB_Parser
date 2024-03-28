from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Запросить отчет')],
    [KeyboardButton(text='Запросить заказ')]
], resize_keyboard=True, input_field_placeholder='Выберите действие...')

report_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить увелечение на 1-ую неделю", url='https://t.me')],
    [InlineKeyboardButton(text="Запросить отчет за другой период", url='https://t.me')]
])
