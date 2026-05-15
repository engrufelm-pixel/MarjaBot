from typing import Sequence
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_ai_content_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ SEO-заголовок", callback_data=f"ai_gen:title:{product_id}")
    builder.button(text="📝 Описание карточки", callback_data=f"ai_gen:description:{product_id}")
    builder.button(text="🎯 5 главных УТП", callback_data=f"ai_gen:utp:{product_id}")
    builder.button(text="💬 Ответы на отзывы", callback_data=f"ai_gen:reviews:{product_id}")
    builder.button(text="🎨 Идеи для инфографики", callback_data=f"ai_gen:infographic:{product_id}")
    builder.button(text="🔑 Ключевые слова", callback_data=f"ai_gen:keywords:{product_id}")
    builder.button(text="◀️ Назад к товару", callback_data=f"product_view:{product_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_ai_product_list_keyboard(products: Sequence) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(text=f"📦 {p.name[:35]}", callback_data=f"ai_select_product:{p.id}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
