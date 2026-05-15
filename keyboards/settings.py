from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💱 Курс юаня (₽/¥)", callback_data="settings_yuan")
    builder.button(text="🚚 Цена карго (₽/кг)", callback_data="settings_cargo")
    builder.button(text="💼 Комиссия WB (%)", callback_data="settings_commission")
    builder.button(text="📊 Налог УСН (%)", callback_data="settings_tax")
    builder.button(text="🤖 API-ключ AITunnel", callback_data="settings_aitunnel")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
