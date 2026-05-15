from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🧮 Быстрый расчет"),
                KeyboardButton(text="📦 Мои товары"),
            ],
            [
                KeyboardButton(text="🤖 AI-Контент"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,
    )
