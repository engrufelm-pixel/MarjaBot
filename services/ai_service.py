import httpx
import json

# ─────────────────────────────────────────────
# Чёрный список фраз для фильтрации ответа AI
# При обнаружении — один автоматический повтор запроса.
# ─────────────────────────────────────────────
BLACKLIST: frozenset[str] = frozenset({
    "скидка", "акция", "первый заказ", "довольных клиентов",
    "лучший", "№1", "подарок", "успей купить", "только сегодня",
    "хит продаж", "распродажа", "гарантия результата",
    "мгновенный эффект", "безопасно для всех",
    "рекомендовано специалистами",
})


def _has_blacklisted(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in BLACKLIST)


# ─────────────────────────────────────────────
# Инфографика: системный + пользовательский промпты
# ─────────────────────────────────────────────
_INFOGRAPHIC_SYSTEM = """\
Ты — senior copywriter и маркетплейс-дизайнер для карточек Wildberries и Ozon.

Твоя задача — создавать ИДЕИ ДЛЯ ИНФОГРАФИКИ карточки товара.
Ты не придумываешь акции, скидки, подарки, отзывы, социальные доказательства \
и рекламные обещания, если этого нет во входных данных.

ВАЖНЫЕ ПРАВИЛА:
1. Все слайды — в едином визуальном стиле. Один стиль на всю карточку.
2. Не предлагай разные цвета для каждого слайда.
3. Не используй: «скидка», «акция», «первый заказ», «лучший», «№1», \
«тысячи довольных клиентов», «хит», «топ», «гарантия результата», \
медицинские и неподтверждённые обещания.
4. Не выдумывай характеристики, которых нет во входных данных.
5. Слайды должны помогать покупателю быстро понять: что это, как работает, \
в чём польза, для кого, как использовать, какие параметры / комплектация.
6. Тексты короткие, понятные, в стиле маркетплейсов, без воды.
7. Не предлагай блоки с отзывами и социальными доказательствами.
8. Пиши с учётом карточки WB/Ozon, а не лендинга.

ФОРМАТ ОТВЕТА — строго JSON, никакого текста вокруг:
{
  "style_note": "описание единого визуального стиля всей карточки (1–2 предложения)",
  "slides": [
    {
      "slide": 1,
      "goal": "цель слайда",
      "title": "заголовок до 45 символов, без эмодзи",
      "subtitle": "подзаголовок до 70 символов, без эмодзи",
      "bullets": ["пункт 1", "пункт 2", "пункт 3"],
      "visual": "что должно быть на изображении"
    }
  ]
}

Ограничения: ровно 5 слайдов, bullets 2–4 пункта, эмодзи только в bullets.\
"""

_INFOGRAPHIC_USER = """\
Сделай идеи для 5 слайдов инфографики карточки товара.

Товар: {product_name}
Категория: {category}
Маркетплейс: Wildberries

Что важно показать:
- польза товара
- как использовать
- для кого подходит
- особенности без громких обещаний
- единый спокойный стиль карточки

Запрещено:
- скидки, акции, «первый заказ»
- отзывы и социальные доказательства
- ложные / неподтверждённые обещания
- разные цвета для каждого слайда\
"""


# ─────────────────────────────────────────────
# Остальные промпты (одно сообщение, роль user)
# ─────────────────────────────────────────────
PROMPTS: dict[str, str] = {
    "title": (
        "Ты — SEO-специалист маркетплейсов WB и Ozon. "
        "Напиши 3 варианта SEO-заголовка для товара «{product_name}» (категория: {category}). "
        "Каждый заголовок до 100 символов, с главными ключевыми словами. "
        "Формат: нумерованный список без вступления."
    ),
    "description": (
        "Ты — копирайтер маркетплейсов. "
        "Напиши продающее описание для товара «{product_name}» (категория: {category}). "
        "Требования: ключевые слова, выгоды покупателя, 200–400 слов, живой язык. "
        "Без скидок, акций и неподтверждённых обещаний."
    ),
    "utp": (
        "Ты — маркетолог маркетплейсов. "
        "Напиши 5 главных УТП для товара «{product_name}» (категория: {category}). "
        "Каждое УТП — одна строка с эмодзи, акцент на пользе покупателя. "
        "Без скидок, акций, «лучший» и громких обещаний."
    ),
    "reviews": (
        "Ты — менеджер по работе с клиентами маркетплейса. "
        "Напиши 3 шаблона ответов на негативные отзывы для товара «{product_name}». "
        "Ответы вежливые, конструктивные, предлагают решение. "
        "Сценарии: производственный брак, товар не подошёл, долгая доставка."
    ),
    "keywords": (
        "Ты — SEO-специалист WB и Ozon. "
        "Подбери 20 ключевых слов для товара «{product_name}» (категория: {category}). "
        "Раздели на 3 группы: высокочастотные (5), среднечастотные (10), низкочастотные (5). "
        "Формат: нумерованный список по группам."
    ),
}


# ─────────────────────────────────────────────
# Форматирование JSON-ответа инфографики → текст для Telegram
# ─────────────────────────────────────────────
def _format_infographic(raw: str) -> str:
    # Ищем JSON даже если вокруг есть лишний текст
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        return raw  # Если JSON не найден — вернуть как есть

    try:
        data = json.loads(raw[start:end])
    except json.JSONDecodeError:
        return raw

    lines: list[str] = []
    style = data.get("style_note", "")
    if style:
        lines.append(f"<i>🎨 Стиль карточки: {style}</i>\n")

    for slide in data.get("slides", []):
        num = slide.get("slide", "?")
        goal = slide.get("goal", "")
        title = slide.get("title", "")
        subtitle = slide.get("subtitle", "")
        bullets = slide.get("bullets", [])
        visual = slide.get("visual", "")

        lines.append(f"<b>Слайд {num}</b> — <i>{goal}</i>")
        if title:
            lines.append(f"Заголовок: <b>{title}</b>")
        if subtitle:
            lines.append(f"Подзаголовок: {subtitle}")
        if bullets:
            for b in bullets:
                lines.append(f"  • {b}")
        if visual:
            lines.append(f"Визуал: {visual}")
        lines.append("")

    return "\n".join(lines).strip()


class AIService:
    def __init__(self, api_key: str, base_url: str = "https://api.aitunnel.ru/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        prompt_type: str,
        product_name: str,
        category: str,
        model: str = "gpt-4o-mini",
    ) -> str:
        if not self.api_key:
            return (
                "⚠️ <b>API-ключ AITunnel не настроен.</b>\n\n"
                "Перейди в ⚙️ <b>Настройки</b> и добавь ключ AITunnel.\n"
                "Получить ключ: <b>aitunnel.ru</b>"
            )

        if prompt_type == "infographic":
            return await self._generate_infographic(product_name, category, model)

        template = PROMPTS.get(prompt_type)
        if not template:
            return "❌ Неизвестный тип запроса."

        prompt = template.format(product_name=product_name, category=category)
        return await self._call_api(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_retries=1,
        )

    async def _generate_infographic(
        self, product_name: str, category: str, model: str
    ) -> str:
        messages = [
            {"role": "system", "content": _INFOGRAPHIC_SYSTEM},
            {
                "role": "user",
                "content": _INFOGRAPHIC_USER.format(
                    product_name=product_name, category=category
                ),
            },
        ]
        raw = await self._call_api(messages=messages, model=model, max_retries=1)
        if raw.startswith("❌") or raw.startswith("⏱") or raw.startswith("🔑") or raw.startswith("🚫"):
            return raw
        return _format_infographic(raw)

    async def _call_api(
        self,
        messages: list[dict],
        model: str,
        max_retries: int = 1,
    ) -> str:
        for attempt in range(max_retries + 1):
            result = await self._request(messages, model)

            # Если ошибка API — сразу вернуть
            if result.startswith("❌") or result.startswith("⏱") or result.startswith("🔑") or result.startswith("🚫"):
                return result

            # Проверяем чёрный список только для нежурналируемых попыток
            if _has_blacklisted(result) and attempt < max_retries:
                continue  # повторяем запрос

            return result

        return result  # возвращаем даже если прошёл с нарушениями (лучше что-то, чем ничего)

    async def _request(self, messages: list[dict], model: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 1800,
                        "temperature": 0.7,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            return "⏱️ Превышено время ожидания. Попробуй ещё раз."
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return "🔑 Неверный API-ключ. Проверь настройки."
            if e.response.status_code == 429:
                return "🚫 Превышен лимит запросов. Подожди немного."
            return f"❌ Ошибка API: {e.response.status_code}"
        except Exception as e:
            return f"❌ Непредвиденная ошибка: {e}"
