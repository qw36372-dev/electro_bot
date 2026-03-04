"""Логика расчёта стоимости электромонтажных работ."""

from database.crud import get_all_settings


async def calculate_price(data: dict) -> tuple[int, int]:
    """
    Рассчитывает вилку стоимости работ.

    Формула:
        base = Σ (количество_позиции × цена_позиции)
        base *= коэффициенты (вторичка, бетон, этажи)
        min  = base × (1 - spread)
        max  = base × (1 + spread)

    :param data: словарь с данными пользователя из FSM
    :returns: (price_min, price_max) в рублях
    """
    cfg = await get_all_settings()

    def p(key: str) -> float:
        return cfg.get(key, 0.0)

    # ── Базовая сумма ────────────────────────────────────────
    base = (
        int(data.get("sockets", 0)) * p("price_socket")
        + int(data.get("switches", 0)) * p("price_switch")
        + int(data.get("spots", 0)) * p("price_spot")
        + int(data.get("lamps_simple", 0)) * p("price_lamp_simple")
        + int(data.get("lamps_hard", 0)) * p("price_lamp_hard")
        + int(data.get("stove", 0)) * p("price_stove")
        + int(data.get("oven", 0)) * p("price_oven")
        + int(data.get("ac", 0)) * p("price_ac")
        + (p("price_boiler") if data.get("boiler") else 0)
        + float(data.get("floor_heating", 0)) * p("price_floor_heating")
        + int(data.get("washing_machine", 0)) * p("price_washing_machine")
        + int(data.get("dishwasher", 0)) * p("price_dishwasher")
        + (p("price_shield") if data.get("shield_needed") else 0)
        + int(data.get("demolition", 0)) * p("price_demolition")
        + (p("price_low_voltage") if data.get("low_voltage") else 0)
    )

    # ── Коэффициенты ────────────────────────────────────────
    coeff = 1.0
    building_type: str = data.get("building_type", "")
    wall_material: str = data.get("wall_material", "")

    if "вторичка" in building_type.lower():
        coeff *= p("coeff_secondary")
    if "бетон" in wall_material.lower():
        coeff *= p("coeff_concrete")
    if "2+" in building_type or "2 " in building_type or "два" in building_type.lower():
        coeff *= p("coeff_floors_2plus")

    base *= coeff

    # ── Вилка ────────────────────────────────────────────────
    spread = p("spread")
    price_min = int(base * (1 - spread))
    price_max = int(base * (1 + spread))

    # Минимальная стоимость — 5 000 ₽
    price_min = max(price_min, 5_000)
    price_max = max(price_max, price_min + 1_000)

    return price_min, price_max
