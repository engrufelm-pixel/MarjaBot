from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)

    # Настройки расчёта
    yuan_rate = Column(Float, default=13.0)
    cargo_price = Column(Float, default=75.0)      # ₽ за кг
    wb_commission = Column(Float, default=15.0)    # %
    tax_rate = Column(Float, default=6.0)          # %
    aitunnel_api_key = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)

    # Входные данные
    purchase_price = Column(Float, nullable=False)
    weight_grams = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)

    # Рассчитанные затраты
    cargo_cost = Column(Float, default=0.0)
    packaging_cost = Column(Float, default=0.0)
    wb_commission_cost = Column(Float, default=0.0)
    wb_logistics_cost = Column(Float, default=0.0)
    advertising_cost = Column(Float, default=0.0)
    tax_cost = Column(Float, default=0.0)
    total_costs = Column(Float, default=0.0)

    # Итог
    net_profit = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
