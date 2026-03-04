"""Inline и reply клавиатуры для пользовательского и административного флоу."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def kb(*rows: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """Вспомогательная функция: создаёт inline-клавиатуру из списка строк [(text, callback_data)]."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=d) for t, d in row]
            for row in rows
        ]
    )


# ── Главное меню ─────────────────────────────────────────────
start_kb = kb([("🔧 Рассчитать стоимость работ", "calc_start")])

# ── Тип объекта ──────────────────────────────────────────────
object_type_kb = kb(
    [("🏢 Квартира", "obj_flat"), ("🏠 Частный дом", "obj_house")]
)

# ── Тип жилья (квартира) ─────────────────────────────────────
building_type_flat_kb = kb(
    [("🆕 Новостройка", "bt_new"), ("🏚 Вторичка", "bt_old")]
)

# ── Этажей (дом) ─────────────────────────────────────────────
building_type_house_kb = kb(
    [("1️⃣ 1 этаж", "bt_1floor"), ("2️⃣ 2+ этажа", "bt_2floor")]
)

# ── Количество комнат ────────────────────────────────────────
rooms_kb = kb(
    [("1", "rooms_1"), ("2", "rooms_2"), ("3", "rooms_3")],
    [("4", "rooms_4"), ("5+", "rooms_5plus")],
)

# ── Материал стен ────────────────────────────────────────────
wall_kb = kb(
    [("🧱 Бетон", "wall_concrete"), ("🏗 Кирпич", "wall_brick")],
    [("🪨 Газоблок/пеноблок", "wall_gas"), ("🪵 Дерево", "wall_wood")],
    [("❓ Другое", "wall_other")],
)

# ── Да / Нет ─────────────────────────────────────────────────
yes_no_kb = kb([("✅ Да", "yn_yes"), ("❌ Нет", "yn_no")])

# ── Способ связи ─────────────────────────────────────────────
contact_kb = kb(
    [("📞 Звонок", "contact_call"), ("💬 WhatsApp", "contact_wa"), ("✈️ Telegram", "contact_tg")]
)

# ── Подтверждение заявки ─────────────────────────────────────
confirm_kb = kb(
    [("📨 Отправить заявку мастеру", "submit_lead")],
    [("✏️ Изменить данные", "edit_data"), ("❌ Отменить", "cancel_lead")],
)

# ── Административное главное меню ────────────────────────────
admin_menu_kb = kb(
    [("💰 Управление ценами", "adm_prices")],
    [("📐 Управление коэффициентами", "adm_coeffs")],
    [("👁 Просмотр настроек", "adm_view")],
    [("📊 Статистика заявок", "adm_stats")],
)


def prices_kb(settings: dict) -> InlineKeyboardMarkup:
    """Клавиатура со списком цен для редактирования."""
    from config import PRICE_LABELS

    rows = []
    for key, label in PRICE_LABELS.items():
        val = int(settings.get(key, 0))
        rows.append([(f"{label} ({val} ₽)", f"edit_price_{key}")])
    rows.append([("⬅️ Назад", "adm_back")])
    return kb(*rows)


def coeffs_kb(settings: dict) -> InlineKeyboardMarkup:
    """Клавиатура со списком коэффициентов для редактирования."""
    from config import COEFF_LABELS

    rows = []
    for key, label in COEFF_LABELS.items():
        val = settings.get(key, 0)
        rows.append([(f"{label} ({val})", f"edit_coeff_{key}")])
    rows.append([("⬅️ Назад", "adm_back")])
    return kb(*rows)
