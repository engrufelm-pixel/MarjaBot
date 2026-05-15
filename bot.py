# Точка входа перенесена в main.py для совместимости с BotHost
# Этот файл оставлен для локального запуска
import asyncio
from main import main

if __name__ == "__main__":
    asyncio.run(main())
