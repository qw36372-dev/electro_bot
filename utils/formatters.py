"""Форматирование сообщений для пользователя и канала."""

from database.models import Lead


def yn(value) -> str:
    """Булево → Да/Нет."""
    return "Да" if value else "Нет"


def format_lead_message(lead: Lead) -> str:
    """Формирует структурированное сообщение для приватного канала."""
    from datetime import timezone

    dt = lead.created_at
    date_str = dt.strftime("%d.%m.%Y %H:%M") if dt else "—"

    username_str = f"@{lead.username}" if lead.username else "—"

    lines = [
        f"📋 <b>Новая заявка #{lead.id}</b>",
        "",
        f"<b>Объект:</b> {lead.object_type} ({lead.building_type})",
        f"<b>Площадь:</b> {lead.area} кв.м",
        f"<b>Комнат:</b> {lead.rooms}",
        f"<b>Стены:</b> {lead.wall_material}",
        "",
        "⚡ <b>Электрические точки:</b>",
        f"• Розетки: {lead.sockets} шт",
        f"• Выключатели: {lead.switches} шт",
        f"• Споты: {lead.spots} шт",
        f"• Люстры простые: {lead.lamps_simple} шт",
        f"• Люстры сложные: {lead.lamps_hard} шт",
        "",
        "🔌 <b>Мощные потребители:</b>",
        f"• Варочная панель: {lead.stove} шт",
        f"• Духовой шкаф: {lead.oven} шт",
        f"• Кондиционеры: {lead.ac} шт",
        f"• Бойлер: {yn(lead.boiler)}",
        f"• Тёплые полы: {lead.floor_heating} кв.м",
        f"• Стиральная машина: {lead.washing_machine} шт",
        f"• Посудомоечная машина: {lead.dishwasher} шт",
        "",
        "🛠 <b>Дополнительно:</b>",
        f"• Сборка щита: {yn(lead.shield_needed)}",
        f"• Слаботочка: {yn(lead.low_voltage)}",
        f"• Демонтаж: {lead.demolition} точек",
        "",
        "💰 <b>Примерная стоимость работ:</b>",
        f"от {lead.price_min:,} до {lead.price_max:,} ₽ (без материалов)".replace(",", " "),
        "",
        "👤 <b>Контакты:</b>",
        f"Имя: {lead.client_name}",
        f"Телефон: {lead.client_phone}",
        f"Связь: {lead.contact_method}",
        f"Telegram: {username_str}",
        "",
        f"📅 <i>Дата заявки: {date_str}</i>",
    ]
    return "\n".join(lines)


def format_summary(data: dict, price_min: int, price_max: int) -> str:
    """Краткая сводка для показа пользователю перед подтверждением."""
    lines = [
        "📊 <b>Ваш расчёт готов!</b>",
        "",
        f"<b>Объект:</b> {data.get('object_type', '—')} ({data.get('building_type', '—')})",
        f"<b>Площадь:</b> {data.get('area', '—')} кв.м, {data.get('rooms', '—')} комнат",
        f"<b>Стены:</b> {data.get('wall_material', '—')}",
        "",
        "⚡ <b>Основные точки:</b>",
        f"Розетки: {data.get('sockets', 0)}, "
        f"Выключатели: {data.get('switches', 0)}, "
        f"Споты: {data.get('spots', 0)}",
        "",
        f"💰 <b>Примерная стоимость работ:</b>",
        f"<b>от {price_min:,} до {price_max:,} ₽</b> (без материалов)".replace(",", "\u00a0"),
        "",
        "<i>Точная смета составляется после осмотра объекта или по вашему проекту. "
        "Осмотр бесплатный.</i>",
    ]
    return "\n".join(lines)


def format_all_settings(settings: dict) -> str:
    """Форматирует все настройки для вывода в админ-панели."""
    from config import COEFF_LABELS, PRICE_LABELS

    lines = ["⚙️ <b>Текущие настройки</b>", "", "💰 <b>Цены:</b>"]
    for key, label in PRICE_LABELS.items():
        val = settings.get(key, "—")
        lines.append(f"  • {label}: {val} ₽")

    lines += ["", "📐 <b>Коэффициенты:</b>"]
    for key, label in COEFF_LABELS.items():
        val = settings.get(key, "—")
        lines.append(f"  • {label}: {val}")

    return "\n".join(lines)
