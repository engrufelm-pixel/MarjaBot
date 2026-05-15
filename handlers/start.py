from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.main import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()

    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        session.add(user)
        await session.commit()

    await message.answer(
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"Я <b>Marja Bot</b> — AI-ассистент селлера маркетплейсов.\n\n"
        f"Что умею:\n"
        f"🧮 Считать прибыль <b>до</b> закупки — не прогоришь\n"
        f"📦 Хранить данные о товарах — не считать каждый раз\n"
        f"🤖 Генерировать контент через AI — карточки, которые продают\n\n"
        f"Выбери раздел:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Справка Marja Bot</b>\n\n"
        "🧮 <b>Быстрый расчёт</b> — считает чистую прибыль и маржу "
        "с учётом карго, комиссии WB, логистики, рекламы и налога УСН.\n\n"
        "📦 <b>Мои товары</b> — список сохранённых товаров. "
        "Можно пересчитать или удалить.\n\n"
        "🤖 <b>AI-Контент</b> — генерирует заголовки, описания, УТП, "
        "ответы на отзывы, идеи для инфографики и ключевые слова.\n\n"
        "⚙️ <b>Настройки</b> — курс юаня, цена карго, комиссия WB, "
        "ставка налога, API-ключ AITunnel.\n\n"
        "/start — вернуться в главное меню\n"
        "/cancel — отменить текущее действие",
        parse_mode="HTML",
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_keyboard(),
    )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "🏠 <b>Главное меню</b>",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()
