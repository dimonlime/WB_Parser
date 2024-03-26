from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Запросить отчет')],
    [KeyboardButton(text='Запросить заказ')]
], resize_keyboard=True, input_field_placeholder='Выберите действие...')
