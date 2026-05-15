from typing import Sequence
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_products_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Список товаров", callback_data="products_list")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_products_list_keyboard(products: Sequence) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        light = "🟢" if p.margin >= 30 else ("🟡" if p.margin >= 15 else "🔴")
        label = f"{light} {p.name[:25]} | {p.net_profit:.0f}₽ | {p.margin:.0f}%"
        builder.button(text=label, callback_data=f"product_view:{p.id}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 AI-Контент", callback_data=f"product_ai:{product_id}")
    builder.button(text="🔄 Пересчитать", callback_data=f"product_recalc:{product_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"product_delete:{product_id}")
    builder.button(text="◀️ К списку", callback_data="products_list")
    builder.adjust(1)
    return builder.as_markup()


def get_delete_confirm_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"product_delete_confirm:{product_id}")
    builder.button(text="❌ Отмена", callback_data=f"product_view:{product_id}")
    builder.adjust(2)
    return builder.as_markup()
