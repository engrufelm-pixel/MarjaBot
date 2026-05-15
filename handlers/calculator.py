from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import MENU_BUTTONS
from database.models import User, Product
from keyboards.calculator import get_category_keyboard, get_save_keyboard
from keyboards.main import get_main_keyboard
from services.calculator import calculate, format_result
from states.calculator import CalculatorStates

router = Router()


# ─────────────────────────────────────────────
# Шаг 1: запуск расчёта
# ─────────────────────────────────────────────

@router.message(F.text == "🧮 Быстрый расчет")
async def start_calculator(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CalculatorStates.waiting_purchase_price)
    await message.answer(
        "🧮 <b>Быстрый расчёт</b>\n\n"
        "Шаг 1/4 — Введи <b>цену закупки</b> за 1 шт. (в ₽)\n\n"
        "Примеры: <code>80</code> · <code>350</code>\n"
        "<i>Если закупаешь в юанях — введи сумму уже пересчитанную в рубли, "
        "или настрой курс в ⚙️ Настройках</i>",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Шаг 2: цена закупки
# ─────────────────────────────────────────────

@router.message(CalculatorStates.waiting_purchase_price, F.text, ~F.text.in_(MENU_BUTTONS))
async def process_purchase_price(message: Message, state: FSMContext) -> None:
    raw = message.text.strip().replace(",", ".").replace("₽", "").replace("¥", "")
    try:
        price = float(raw)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи корректную цену (только число, например: <code>80</code>)", parse_mode="HTML")
        return

    await state.update_data(purchase_price=price)
    await state.set_state(CalculatorStates.waiting_weight)
    await message.answer(
        f"✅ Цена закупки: <b>{price:.0f}₽</b>\n\n"
        f"Шаг 2/4 — Введи <b>вес 1 шт. в граммах</b>\n\n"
        f"Пример: <code>300</code>",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Шаг 3: вес
# ─────────────────────────────────────────────

@router.message(CalculatorStates.waiting_weight, F.text, ~F.text.in_(MENU_BUTTONS))
async def process_weight(message: Message, state: FSMContext) -> None:
    raw = message.text.strip().replace(",", ".").replace("г", "").replace("g", "").replace("кг", "")
    try:
        weight = float(raw)
        if weight <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи вес в граммах (только число, например: <code>300</code>)", parse_mode="HTML")
        return

    await state.update_data(weight=weight)
    await state.set_state(CalculatorStates.waiting_sell_price)
    await message.answer(
        f"✅ Вес: <b>{weight:.0f}г</b>\n\n"
        f"Шаг 3/4 — Введи <b>планируемую цену продажи</b> на WB/Ozon (в ₽)\n\n"
        f"Пример: <code>799</code>",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Шаг 4: цена продажи
# ─────────────────────────────────────────────

@router.message(CalculatorStates.waiting_sell_price, F.text, ~F.text.in_(MENU_BUTTONS))
async def process_sell_price(message: Message, state: FSMContext) -> None:
    raw = message.text.strip().replace(",", ".").replace("₽", "")
    try:
        price = float(raw)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи корректную цену продажи (например: <code>799</code>)", parse_mode="HTML")
        return

    await state.update_data(sell_price=price)
    await state.set_state(CalculatorStates.waiting_category)
    await message.answer(
        f"✅ Цена продажи: <b>{price:.0f}₽</b>\n\n"
        f"Шаг 4/4 — Выбери <b>категорию товара</b>:",
        reply_markup=get_category_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Шаг 5: категория → расчёт
# ─────────────────────────────────────────────

@router.callback_query(CalculatorStates.waiting_category, F.data.startswith("calc_cat:"))
async def process_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    category = callback.data.split(":", 1)[1]
    data = await state.get_data()

    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one_or_none()
    cargo_price = user.cargo_price if user else 75.0
    wb_commission = user.wb_commission if user else 15.0
    tax_rate = user.tax_rate if user else 6.0

    calc = calculate(
        purchase_price=data["purchase_price"],
        weight_grams=data["weight"],
        sell_price=data["sell_price"],
        category=category,
        cargo_price_per_kg=cargo_price,
        wb_commission_pct=wb_commission,
        tax_rate_pct=tax_rate,
    )

    recalc_id: int | None = data.get("recalc_product_id")
    await state.update_data(calc_result=calc.__dict__, category=category)
    # Не устанавливаем waiting_product_name здесь — только при явном нажатии «Сохранить»
    await state.set_state(None)

    await callback.message.edit_text(
        format_result(calc),
        reply_markup=get_save_keyboard(recalc_product_id=recalc_id),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────────────────────────
# Кнопка «Сохранить товар» — запрашиваем название
# ─────────────────────────────────────────────

@router.callback_query(F.data == "calc_save")
async def ask_product_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CalculatorStates.waiting_product_name)
    await callback.message.answer(
        "💾 Введи <b>название товара</b> для сохранения:\n\n"
        "Пример: <code>Лежанка плюшевая серая</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(CalculatorStates.waiting_product_name, F.text, ~F.text.in_(MENU_BUTTONS))
async def save_product(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Попробуй ещё раз.")
        return

    data = await state.get_data()
    cr = data.get("calc_result")
    if not cr:
        await state.clear()
        await message.answer(
            "❌ Данные расчёта не найдены. Начни новый расчёт.",
            reply_markup=get_main_keyboard(),
        )
        return

    product = Product(
        user_telegram_id=message.from_user.id,
        name=name,
        category=cr["category"],
        purchase_price=cr["purchase_price"],
        weight_grams=cr["weight_grams"],
        sell_price=cr["sell_price"],
        cargo_cost=cr["cargo_cost"],
        packaging_cost=cr["packaging_cost"],
        wb_commission_cost=cr["wb_commission_cost"],
        wb_logistics_cost=cr["wb_logistics_cost"],
        advertising_cost=cr["advertising_cost"],
        tax_cost=cr["tax_cost"],
        total_costs=cr["total_costs"],
        net_profit=cr["net_profit"],
        margin=cr["margin"],
    )
    session.add(product)
    await session.commit()
    await state.clear()

    light = "🟢" if cr["margin"] >= 30 else ("🟡" if cr["margin"] >= 15 else "🔴")
    await message.answer(
        f"✅ <b>Товар сохранён!</b>\n\n"
        f"{light} <b>{name}</b>\n"
        f"Прибыль: {cr['net_profit']:.0f}₽ | Маржа: {cr['margin']:.0f}%\n\n"
        f"Найдёшь его в разделе 📦 <b>Мои товары</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# Кнопка «Обновить товар» (при пересчёте)
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("calc_update:"))
async def update_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    cr = data.get("calc_result")

    if not cr:
        await callback.answer("❌ Данные расчёта не найдены.", show_alert=True)
        return

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

    product.category = cr["category"]
    product.purchase_price = cr["purchase_price"]
    product.weight_grams = cr["weight_grams"]
    product.sell_price = cr["sell_price"]
    product.cargo_cost = cr["cargo_cost"]
    product.packaging_cost = cr["packaging_cost"]
    product.wb_commission_cost = cr["wb_commission_cost"]
    product.wb_logistics_cost = cr["wb_logistics_cost"]
    product.advertising_cost = cr["advertising_cost"]
    product.tax_cost = cr["tax_cost"]
    product.total_costs = cr["total_costs"]
    product.net_profit = cr["net_profit"]
    product.margin = cr["margin"]
    await session.commit()
    await state.clear()

    light = "🟢" if cr["margin"] >= 30 else ("🟡" if cr["margin"] >= 15 else "🔴")
    await callback.message.answer(
        f"✅ <b>Товар обновлён!</b>\n\n"
        f"{light} <b>{product.name}</b>\n"
        f"Прибыль: {cr['net_profit']:.0f}₽ | Маржа: {cr['margin']:.0f}%",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─────────────────────────────────────────────
# Кнопка «Новый расчёт»
# ─────────────────────────────────────────────

@router.callback_query(F.data == "calc_new")
async def new_calculation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CalculatorStates.waiting_purchase_price)
    await callback.message.answer(
        "🧮 <b>Новый расчёт</b>\n\n"
        "Шаг 1/4 — Введи <b>цену закупки</b> за 1 шт. (в ₽):",
        parse_mode="HTML",
    )
    await callback.answer()
