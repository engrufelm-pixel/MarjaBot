from dataclasses import dataclass

# Логистика WB зависит от веса (упрощённая шкала)
_WB_LOGISTICS: list[tuple[float, float]] = [
    (500.0, 80.0),
    (1000.0, 100.0),
    (5000.0, 150.0),
    (float("inf"), 200.0),
]

PACKAGING_COST = 15.0       # фиксированная упаковка
ADVERTISING_RATE = 0.10     # 10% от цены продажи


@dataclass
class CalcResult:
    purchase_price: float
    weight_grams: float
    sell_price: float
    category: str
    commission_pct: float
    cargo_cost: float
    packaging_cost: float
    wb_commission_cost: float
    wb_logistics_cost: float
    advertising_cost: float
    tax_cost: float
    total_costs: float
    net_profit: float
    margin: float

    @property
    def verdict(self) -> str:
        if self.margin >= 30:
            return "🟢 ОТЛИЧНЫЙ ТОВАР, БЕРИ!"
        if self.margin >= 15:
            return "🟡 НА ГРАНИ — ПОДУМАЙ!"
        return "🔴 НЕ ВЗДУМАЙ, УЙДЁШЬ В МИНУС!"

    @property
    def traffic_light(self) -> str:
        if self.margin >= 30:
            return "🟢"
        if self.margin >= 15:
            return "🟡"
        return "🔴"


def _wb_logistics(weight_grams: float) -> float:
    for limit, cost in _WB_LOGISTICS:
        if weight_grams <= limit:
            return cost
    return 200.0


def calculate(
    purchase_price: float,
    weight_grams: float,
    sell_price: float,
    category: str,
    cargo_price_per_kg: float = 75.0,
    wb_commission_pct: float = 15.0,
    tax_rate_pct: float = 6.0,
) -> CalcResult:
    weight_kg = weight_grams / 1000.0

    cargo = round(weight_kg * cargo_price_per_kg, 2)
    packaging = PACKAGING_COST
    commission = round(sell_price * wb_commission_pct / 100, 2)
    logistics = _wb_logistics(weight_grams)
    advertising = round(sell_price * ADVERTISING_RATE, 2)
    tax = round(sell_price * tax_rate_pct / 100, 2)

    total = round(purchase_price + cargo + packaging + commission + logistics + advertising + tax, 2)
    net_profit = round(sell_price - total, 2)
    margin = round(net_profit / sell_price * 100, 1) if sell_price > 0 else 0.0

    return CalcResult(
        purchase_price=purchase_price,
        weight_grams=weight_grams,
        sell_price=sell_price,
        category=category,
        commission_pct=wb_commission_pct,
        cargo_cost=cargo,
        packaging_cost=packaging,
        wb_commission_cost=commission,
        wb_logistics_cost=logistics,
        advertising_cost=advertising,
        tax_cost=tax,
        total_costs=total,
        net_profit=net_profit,
        margin=margin,
    )


def format_result(r: CalcResult) -> str:
    weight_kg = r.weight_grams / 1000.0
    return (
        f"🧮 <b>РАЗБОР ПОЛЕТОВ:</b>\n\n"
        f"Себестоимость: {r.purchase_price:.0f}₽\n"
        f"Карго ({weight_kg:.3g}кг × {r.cargo_cost / weight_kg:.0f}₽): {r.cargo_cost:.0f}₽\n"
        f"Упаковка: {r.packaging_cost:.0f}₽\n"
        f"Комиссия WB ({r.commission_pct:.0f}%): {r.wb_commission_cost:.0f}₽\n"
        f"Логистика WB: {r.wb_logistics_cost:.0f}₽\n"
        f"Реклама (10%): {r.advertising_cost:.0f}₽\n"
        f"Налог УСН ({r.tax_cost / r.sell_price * 100:.0f}%): {r.tax_cost:.0f}₽\n"
        f"─────────────────\n"
        f"<b>Полные затраты: {r.total_costs:.0f}₽</b>\n\n"
        f"💰 <b>Чистая прибыль: {r.net_profit:.0f}₽ с шт.</b>\n"
        f"📈 <b>Маржа: {r.margin:.0f}%</b>\n\n"
        f"🚦 <b>Вердикт:</b> {r.verdict}"
    )
