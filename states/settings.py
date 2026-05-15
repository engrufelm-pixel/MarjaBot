from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_yuan_rate = State()
    waiting_cargo_price = State()
    waiting_wb_commission = State()
    waiting_tax_rate = State()
    waiting_aitunnel_key = State()
