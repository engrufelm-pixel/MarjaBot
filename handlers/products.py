from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product
from keyboards.products import (
    get_products_menu_keyboard,
    get_products_list_keyboard,
    get_product_detail_keyboard,
    get_delete_confirm_keyboard,
)
from keyboards.main import get_main_keyboard
from states.calculator import CalculatorStates

router = Router()


@router.message(F.text == "📦 Мои товары")
async def my_products(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "📦 <b>Мои товары</b>\n\n"
        "Здесь хранятся все твои рассчитанные товары.\n"
        "Рассчитай товар в 🧮 <b>Быстром расчёте</b> и сохрани его.",
        reply_markup=get_products_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "products_list")
async def show_products_list(callback: CallbackQuery, session: AsyncSession) -> None:
    result = await session.execute(
        select(Product)
        .where(Product.user_telegram_id == callback.from_user.id)
        .order_by(Product.created_at.desc())
    )
    products = result.scalars().all()

    if not products:
        await callback.message.edit_text(
            "📦 <b>Список товаров пуст</b>\n\n"
            "Используй 🧮 <b>Быстрый расчёт</b> и сохрани результат.",
            reply_markup=get_products_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📦 <b>Мои товары</b> — {len(products)} шт.\n\n"
        f"🟢 ≥30% | 🟡 15–30% | 🔴 &lt;15%\n\n"
        f"Нажми на товар для деталей:",
        reply_markup=get_products_list_keyboard(products),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_view:"))
async def view_product(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])

    result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_telegram_id == callback.from_user.id,
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    light = "🟢" if product.margin >= 30 else ("🟡" if product.margin >= 15 else "🔴")
    text = (
        f"{light} <b>{product.name}</b>\n"
        f"Категория: {product.category}\n\n"
        f"Цена закупки: {product.purchase_price:.0f}₽\n"
        f"Вес: {product.weight_grams:.0f}г\n"
        f"Цена продажи: {product.sell_price:.0f}₽\n\n"
        f"Карго: {product.cargo_cost:.0f}₽\n"
        f"Упаковка: {product.packaging_cost:.0f}₽\n"
        f"Комиссия WB: {product.wb_commission_cost:.0f}₽\n"
        f"Логистика WB: {product.wb_logistics_cost:.0f}₽\n"
        f"Реклама: {product.advertising_cost:.0f}₽\n"
        f"Налог УСН: {product.tax_cost:.0f}₽\n"
        f"─────────────────\n"
        f"Затраты: <b>{product.total_costs:.0f}₽</b>\n\n"
        f"💰 <b>Прибыль: {product.net_profit:.0f}₽</b>\n"
        f"📈 <b>Маржа: {product.margin:.0f}%</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_product_detail_keyboard(product_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_recalc:"))
async def recalc_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])

    result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_telegram_id == callback.from_user.id,
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    await state.clear()
    await state.update_data(recalc_product_id=product_id)
    await state.set_state(CalculatorStates.waiting_purchase_price)

    await callback.message.answer(
        f"🔄 <b>Пересчёт: {product.name}</b>\n\n"
        f"Текущие данные:\n"
        f"• Закупка: {product.purchase_price:.0f}₽\n"
        f"• Вес: {product.weight_grams:.0f}г\n"
        f"• Продажа: {product.sell_price:.0f}₽\n\n"
        f"Шаг 1/4 — Введи <b>новую цену закупки</b> (или старую, если не изменилась):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_delete:"))
async def confirm_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])

    result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_telegram_id == callback.from_user.id,
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    await callback.message.edit_text(
        f"🗑️ Удалить товар <b>{product.name}</b>?\n\n"
        f"Это действие нельзя отменить.",
        reply_markup=get_delete_confirm_keyboard(product_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_delete_confirm:"))
async def delete_product(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])

    await session.execute(
        delete(Product).where(
            Product.id == product_id,
            Product.user_telegram_id == callback.from_user.id,
        )
    )
    await session.commit()

    await callback.message.edit_text(
        "✅ <b>Товар удалён.</b>",
        reply_markup=get_products_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("Товар удалён")
