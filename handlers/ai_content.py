from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import AITUNNEL_API_KEY, AITUNNEL_BASE_URL
from database.models import Product, User
from keyboards.ai_content import get_ai_content_keyboard, get_ai_product_list_keyboard
from keyboards.menu import get_main_keyboard
from services.ai_service import AIService

router = Router()

AI_LABELS: dict[str, str] = {
    "title": "✍️ SEO-заголовок",
    "description": "📝 Описание карточки",
    "utp": "🎯 5 главных УТП",
    "reviews": "💬 Ответы на отзывы",
    "infographic": "🎨 Идеи для инфографики",
    "keywords": "🔑 Ключевые слова",
}


@router.message(F.text == "🤖 AI-Контент")
async def ai_content_menu(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()

    result = await session.execute(
        select(Product)
        .where(Product.user_telegram_id == message.from_user.id)
        .order_by(Product.created_at.desc())
    )
    products = result.scalars().all()

    if not products:
        await message.answer(
            "🤖 <b>AI-Контент</b>\n\n"
            "У тебя пока нет сохранённых товаров.\n\n"
            "Сначала рассчитай товар в 🧮 <b>Быстром расчёте</b> и сохрани его — "
            "тогда AI сможет сгенерировать контент.",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML",
        )
        return

    await message.answer(
        "🤖 <b>AI-Контент</b>\n\n"
        "Выбери товар, для которого хочешь сгенерировать контент:",
        reply_markup=get_ai_product_list_keyboard(products),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("ai_select_product:"))
async def select_product_for_ai(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])
    await _show_ai_menu(callback, session, product_id)


@router.callback_query(F.data.startswith("product_ai:"))
async def product_ai_from_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    product_id = int(callback.data.split(":")[1])
    await _show_ai_menu(callback, session, product_id)


async def _show_ai_menu(callback: CallbackQuery, session: AsyncSession, product_id: int) -> None:
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
        f"🤖 <b>AI-Контент</b>\n\n"
        f"📦 Товар: <b>{product.name}</b>\n"
        f"Категория: {product.category}\n\n"
        f"Что сгенерировать?",
        reply_markup=get_ai_content_keyboard(product_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ai_gen:"))
async def generate_ai_content(callback: CallbackQuery, session: AsyncSession) -> None:
    _, prompt_type, product_id_str = callback.data.split(":", 2)
    product_id = int(product_id_str)

    product_result = await session.execute(
        select(Product).where(
            Product.id == product_id,
            Product.user_telegram_id == callback.from_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    user_result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = user_result.scalar_one_or_none()
    api_key = (user.aitunnel_api_key if user and user.aitunnel_api_key else AITUNNEL_API_KEY) or ""

    label = AI_LABELS.get(prompt_type, "Генерация")

    await callback.message.edit_text(
        f"⏳ <b>Генерирую: {label}</b>\n\n"
        f"Товар: {product.name}\n"
        f"Подожди несколько секунд...",
        parse_mode="HTML",
    )
    await callback.answer()

    ai = AIService(api_key=api_key, base_url=AITUNNEL_BASE_URL)
    content = await ai.generate(
        prompt_type=prompt_type,
        product_name=product.name,
        category=product.category,
    )

    # Telegram ограничивает сообщение 4096 символами
    max_len = 3800
    if len(content) > max_len:
        content = content[:max_len] + "\n\n<i>...текст обрезан</i>"

    await callback.message.edit_text(
        f"🤖 <b>{label}</b>\n"
        f"<i>Товар: {product.name}</i>\n\n"
        f"{content}",
        reply_markup=get_ai_content_keyboard(product_id),
        parse_mode="HTML",
    )
