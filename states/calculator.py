from aiogram.fsm.state import State, StatesGroup


class CalculatorStates(StatesGroup):
    waiting_purchase_price = State()
    waiting_weight = State()
    waiting_sell_price = State()
    waiting_category = State()
    waiting_product_name = State()  # только для сохранения нового товара
