"""Форматирование сообщений для пользователя и канала."""

from database.models import Lead


def yn(value) -> str:
    return "Да" if value else "Нет"


def format_lead_message(lead: Lead) -> str:
    dt = lead.created_at
    date_str = dt.strftime("%d.%m.%Y %H:%M") if dt else "—"
    username_str = f"@{lead.username}" if lead.username else "—"

    # Комнаты: 0 = студия
    rooms_str = "Студия" if lead.rooms == 0 else str(lead.rooms)

    lines = [
        f"📋 <b>Новая заявка #{lead.id}</b>",
        "",
        f"📍 <b>Город:</b> {lead.city or '—'}",
        f"🗺 <b>Район/ЖК:</b> {lead.district or '—'}",
        "",
        f"<b>Объект:</b> {lead.object_type} ({lead.building_type})",
        f"<b>Площадь:</b> {lead.area} кв.м",
        f"<b>Комнат:</b> {rooms_str}",
        f"<b>Стены:</b> {lead.wall_material}",
    ]

    # Работы на участке — только если есть
    if lead.outdoor_work and lead.outdoor_work != "Нет":
        lines.append(f"🌿 <b>Работы на участке:</b> {lead.outdoor_work}")

    lines += [
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
    ]

    if lead.extra_info:
        lines += [
            "💬 <b>Дополнительные сведения мастеру:</b>",
            lead.extra_info,
            "",
        ]

    lines += [
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
    rooms_val = data.get("rooms", "—")
    rooms_str = "Студия" if rooms_val == 0 else str(rooms_val)

    outdoor = data.get("outdoor_work", "")
    outdoor_line = f"\n🌿 <b>Участок:</b> {outdoor}" if outdoor and outdoor != "Нет" else ""

    lines = [
        "📊 <b>Ваш расчёт готов!</b>",
        "",
        f"📍 {data.get('city', '—')}, {data.get('district', '—')}",
        f"<b>Объект:</b> {data.get('object_type', '—')} ({data.get('building_type', '—')})",
        f"<b>Площадь:</b> {data.get('area', '—')} кв.м, комнат: {rooms_str}",
        f"<b>Стены:</b> {data.get('wall_material', '—')}",
    ]
    if outdoor_line:
        lines.append(outdoor_line.strip())

    lines += [
        "",
        "⚡ <b>Основные точки:</b>",
        f"Розетки: {data.get('sockets', 0)}, "
        f"Выключатели: {data.get('switches', 0)}, "
        f"Споты: {data.get('spots', 0)}",
        "",
        "💰 <b>Примерная стоимость работ:</b>",
        f"<b>от {price_min:,} до {price_max:,} ₽</b> (без материалов)".replace(",", "\u00a0"),
        "",
        "<i>Точная смета составляется после осмотра объекта или по вашему проекту. "
        "Осмотр бесплатный.</i>",
    ]
    extra = data.get("extra_info", "")
    if extra:
        lines += ["", "💬 <b>Ваши пожелания мастеру:</b>", extra]
    return "\n".join(lines)


def format_all_settings(settings: dict) -> str:
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
