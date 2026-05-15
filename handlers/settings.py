from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import MENU_BUTTONS
from database.models import User
from keyboards.settings import get_settings_keyboard
from keyboards.menu import get_main_keyboard
from states.settings import SettingsStates

router = Router()


# ─────────────────────────────────────────────
# Главная страница настроек
# ─────────────────────────────────────────────

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await _send_settings(message, session)


async def _send_settings(message: Message, session: AsyncSession) -> None:
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()

    yuan = user.yuan_rate if user else 13.0
    cargo = user.cargo_price if user else 75.0
    comm = user.wb_commission if user else 15.0
    tax = user.tax_rate if user else 6.0
    has_key = "✅ Установлен" if (user and user.aitunnel_api_key) else "❌ Не установлен"

    await message.answer(
        f"⚙️ <b>Настройки расчёта</b>\n\n"
        f"💱 Курс юаня: <b>{yuan}₽/¥</b>\n"
        f"🚚 Цена карго: <b>{cargo}₽/кг</b>\n"
        f"💼 Комиссия WB: <b>{comm}%</b>\n"
        f"📊 Налог УСН: <b>{tax}%</b>\n"
        f"🤖 API AITunnel: <b>{has_key}</b>\n\n"
        f"Нажми на параметр, чтобы изменить:",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Курс юаня
# ─────────────────────────────────────────────

@router.callback_query(F.data == "settings_yuan")
async def set_yuan(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_yuan_rate)
    await callback.message.answer(
        "💱 Введи новый <b>курс юаня</b> (₽ за 1 ¥):\n\n"
        "Пример: <code>13.5</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_yuan_rate, F.text, ~F.text.in_(MENU_BUTTONS))
async def save_yuan(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        rate = float(message.text.strip().replace(",", "."))
        if not (1 <= rate <= 1000):
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи корректный курс (например: <code>13.5</code>)", parse_mode="HTML")
        return

    await _update_setting(session, message.from_user.id, "yuan_rate", rate)
    await state.clear()
    await message.answer(
        f"✅ Курс юаня обновлён: <b>{rate}₽/¥</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Цена карго
# ─────────────────────────────────────────────

@router.callback_query(F.data == "settings_cargo")
async def set_cargo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_cargo_price)
    await callback.message.answer(
        "🚚 Введи новую <b>цену карго</b> (₽ за кг):\n\n"
        "Пример: <code>75</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_cargo_price, F.text, ~F.text.in_(MENU_BUTTONS))
async def save_cargo(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи корректную цену (например: <code>75</code>)", parse_mode="HTML")
        return

    await _update_setting(session, message.from_user.id, "cargo_price", price)
    await state.clear()
    await message.answer(
        f"✅ Цена карго обновлена: <b>{price}₽/кг</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Комиссия WB
# ─────────────────────────────────────────────

@router.callback_query(F.data == "settings_commission")
async def set_commission(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_wb_commission)
    await callback.message.answer(
        "💼 Введи новую <b>комиссию WB</b> (%):\n\n"
        "Пример: <code>15</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_wb_commission, F.text, ~F.text.in_(MENU_BUTTONS))
async def save_commission(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        pct = float(message.text.strip().replace(",", ".").replace("%", ""))
        if not (0 <= pct <= 100):
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи процент от 0 до 100 (например: <code>15</code>)", parse_mode="HTML")
        return

    await _update_setting(session, message.from_user.id, "wb_commission", pct)
    await state.clear()
    await message.answer(
        f"✅ Комиссия WB обновлена: <b>{pct}%</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Налог УСН
# ─────────────────────────────────────────────

@router.callback_query(F.data == "settings_tax")
async def set_tax(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_tax_rate)
    await callback.message.answer(
        "📊 Введи новую <b>ставку налога УСН</b> (%):\n\n"
        "Пример: <code>6</code> (доходы) или <code>15</code> (доходы минус расходы)",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_tax_rate, F.text, ~F.text.in_(MENU_BUTTONS))
async def save_tax(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        rate = float(message.text.strip().replace(",", ".").replace("%", ""))
        if not (0 <= rate <= 100):
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи процент от 0 до 100 (например: <code>6</code>)", parse_mode="HTML")
        return

    await _update_setting(session, message.from_user.id, "tax_rate", rate)
    await state.clear()
    await message.answer(
        f"✅ Налог УСН обновлён: <b>{rate}%</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# API-ключ AITunnel
# ─────────────────────────────────────────────

@router.callback_query(F.data == "settings_aitunnel")
async def set_aitunnel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_aitunnel_key)
    await callback.message.answer(
        "🤖 Введи <b>API-ключ AITunnel</b>:\n\n"
        "Получить ключ: <b>aitunnel.ru</b>\n"
        "Формат: <code>sk-...</code>\n\n"
        "Введи <code>удалить</code>, чтобы убрать ключ.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_aitunnel_key, F.text, ~F.text.in_(MENU_BUTTONS))
async def save_aitunnel(message: Message, state: FSMContext, session: AsyncSession) -> None:
    key = message.text.strip()

    if key.lower() in ("удалить", "delete", "remove"):
        await _update_setting(session, message.from_user.id, "aitunnel_api_key", None)
        await state.clear()
        await message.answer("✅ API-ключ удалён.", reply_markup=get_main_keyboard())
        return

    if len(key) < 10:
        await message.answer("❌ Ключ слишком короткий. Введи полный API-ключ.")
        return

    await _update_setting(session, message.from_user.id, "aitunnel_api_key", key)
    await state.clear()
    await message.answer(
        "✅ <b>API-ключ AITunnel сохранён!</b>\n\n"
        "Теперь AI-Контент будет работать.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Вспомогательная функция обновления настройки
# ─────────────────────────────────────────────

async def _update_setting(session: AsyncSession, telegram_id: int, field: str, value) -> None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        setattr(user, field, value)
        await session.commit()
