"""Конфигурация бота: токен, ID администраторов, дефолтные цены и коэффициенты."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("API_TOKEN", "")
def _parse_admin_ids() -> list:
    raw = os.getenv("ADMIN_IDS", "")
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            result.append(int(part))
    return result

ADMIN_IDS: list = _parse_admin_ids()
LEADS_CHANNEL_ID: str = os.getenv("LEADS_CHANNEL_ID", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

# ── Базовые цены (₽) — используются при первом запуске ──────
DEFAULT_PRICES: dict[str, float] = {
    "price_socket": 350,
    "price_switch": 300,
    "price_spot": 400,
    "price_lamp_simple": 900,
    "price_lamp_hard": 1500,
    "price_stove": 2000,
    "price_oven": 1500,
    "price_ac": 3000,
    "price_boiler": 2500,
    "price_floor_heating": 800,   # за кв.м
    "price_washing_machine": 1200,
    "price_dishwasher": 1200,
    "price_shield": 8000,
    "price_demolition": 150,
    "price_low_voltage": 5000,
}

# ── Базовые коэффициенты ─────────────────────────────────────
DEFAULT_COEFFICIENTS: dict[str, float] = {
    "coeff_secondary": 1.15,   # вторичка
    "coeff_concrete": 1.10,    # бетонные стены
    "coeff_floors_2plus": 1.20,  # дом 2+ этажа
    "spread": 0.10,            # ±10 % разброс
}

# Читаемые названия для админ-панели
PRICE_LABELS: dict[str, str] = {
    "price_socket": "Розетка",
    "price_switch": "Выключатель",
    "price_spot": "Точечный светильник",
    "price_lamp_simple": "Люстра простая",
    "price_lamp_hard": "Люстра сложная",
    "price_stove": "Варочная панель",
    "price_oven": "Духовой шкаф",
    "price_ac": "Кондиционер",
    "price_boiler": "Бойлер",
    "price_floor_heating": "Тёплые полы (за кв.м)",
    "price_washing_machine": "Стиральная машина",
    "price_dishwasher": "Посудомоечная машина",
    "price_shield": "Сборка щита",
    "price_demolition": "Демонтаж (за точку)",
    "price_low_voltage": "Слаботочка (комплект)",
}

COEFF_LABELS: dict[str, str] = {
    "coeff_secondary": "Коэффициент «Вторичка»",
    "coeff_concrete": "Коэффициент «Бетонные стены»",
    "coeff_floors_2plus": "Коэффициент «Дом 2+ этажа»",
    "spread": "Разброс цены (доля, напр. 0.10 = ±10%)",
}

# Антиспам: минимальный интервал между заявками (секунды)
SPAM_INTERVAL: int = 300
