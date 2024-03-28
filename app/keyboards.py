from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Запросить отчет')],
    [KeyboardButton(text='Запросить заказ')]
], resize_keyboard=True, input_field_placeholder='Выберите действие...')

report_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить увелечение на 1-ую неделю", callback_data='increase_w1')],
    [InlineKeyboardButton(text="Добавить увелечение на 2-ую неделю", callback_data='increase_w2')],
    [InlineKeyboardButton(text="Поставки 1-я неделя", callback_data='shipment_w1')],
    [InlineKeyboardButton(text="Поставки 2-я неделя", callback_data='shipment_w2')],
    [InlineKeyboardButton(text="Запросить отчет", callback_data='generate_report')]
])
