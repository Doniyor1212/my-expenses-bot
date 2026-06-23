from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Баланс"), KeyboardButton(text="Отчет")],
            [KeyboardButton(text="Статистика"), KeyboardButton(text="Бюджет")],
            [KeyboardButton(text="Цели"), KeyboardButton(text="AI-анализ")],
            [KeyboardButton(text="График"), KeyboardButton(text="История")],
        ],
        resize_keyboard=True
    )
