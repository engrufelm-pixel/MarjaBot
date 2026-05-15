import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
AITUNNEL_API_KEY: str = os.getenv("AITUNNEL_API_KEY", "")
AITUNNEL_BASE_URL: str = os.getenv("AITUNNEL_BASE_URL", "https://api.aitunnel.ru/v1")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./marja_bot.db")

# Кнопки главного меню — используются для фильтрации в FSM
MENU_BUTTONS = frozenset({
    "🧮 Быстрый расчет",
    "📦 Мои товары",
    "🤖 AI-Контент",
    "⚙️ Настройки",
})
