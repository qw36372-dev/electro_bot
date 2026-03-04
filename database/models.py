"""SQLAlchemy-модели: таблицы settings и leads."""

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Setting(Base):
    """Хранит цены и коэффициенты с поддержкой динамического изменения."""

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(Text, unique=True, nullable=False)
    value = Column(Float, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Lead(Base):
    """Заявка от пользователя."""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    username = Column(Text)

    object_type = Column(Text)       # квартира / дом
    building_type = Column(Text)     # новостройка / вторичка / 1этаж / 2+этажа

    area = Column(Float)
    rooms = Column(Integer)
    wall_material = Column(Text)

    sockets = Column(Integer, default=0)
    switches = Column(Integer, default=0)
    spots = Column(Integer, default=0)
    lamps_simple = Column(Integer, default=0)
    lamps_hard = Column(Integer, default=0)

    stove = Column(Integer, default=0)
    oven = Column(Integer, default=0)
    ac = Column(Integer, default=0)
    boiler = Column(Boolean, default=False)
    floor_heating = Column(Float, default=0.0)
    washing_machine = Column(Integer, default=0)
    dishwasher = Column(Integer, default=0)

    shield_needed = Column(Boolean, default=False)
    low_voltage = Column(Boolean, default=False)
    demolition = Column(Integer, default=0)

    price_min = Column(Integer)
    price_max = Column(Integer)

    client_name = Column(Text)
    client_phone = Column(Text)
    contact_method = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
