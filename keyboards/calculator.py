from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

CATEGORIES = ["Одежда", "Дом", "Зоотовары", "Электроника"]


def get_category_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        builder.button(text=cat, callback_data=f"calc_cat:{cat}")
    builder.adjust(2)
    return builder.as_markup()


def get_save_keyboard(recalc_product_id: int | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if recalc_product_id:
        builder.button(
            text="💾 Обновить товар",
            callback_data=f"calc_update:{recalc_product_id}",
        )
    else:
        builder.button(text="💾 Сохранить товар", callback_data="calc_save")
    builder.button(text="🔄 Новый расчёт", callback_data="calc_new")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
