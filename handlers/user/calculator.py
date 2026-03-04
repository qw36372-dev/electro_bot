"""Основной флоу калькулятора: FSM от выбора объекта до контактов."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import (
    building_type_flat_kb,
    building_type_house_kb,
    contact_kb,
    object_type_kb,
    rooms_kb,
    wall_kb,
    yes_no_kb,
)
from states import CalcStates
from utils.validators import (
    sanitize_text,
    validate_phone,
    validate_positive_integer,
    validate_positive_number,
)

router = Router(name="calculator")
log = logging.getLogger(__name__)


# ── Запуск калькулятора ──────────────────────────────────────

@router.callback_query(F.data == "calc_start")
async def cb_calc_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CalcStates.choose_object_type)
    await call.message.edit_text(
        "🏗 <b>Выберите тип объекта:</b>",
        reply_markup=object_type_kb,
        parse_mode="HTML",
    )


# ── Тип объекта ──────────────────────────────────────────────

@router.callback_query(CalcStates.choose_object_type, F.data.in_({"obj_flat", "obj_house"}))
async def cb_object_type(call: CallbackQuery, state: FSMContext) -> None:
    is_flat = call.data == "obj_flat"
    await state.update_data(object_type="квартира" if is_flat else "дом")
    await state.set_state(CalcStates.choose_building_type)

    if is_flat:
        await call.message.edit_text(
            "🏠 <b>Тип жилья:</b>",
            reply_markup=building_type_flat_kb,
            parse_mode="HTML",
        )
    else:
        await call.message.edit_text(
            "🏚 <b>Количество этажей:</b>",
            reply_markup=building_type_house_kb,
            parse_mode="HTML",
        )


# ── Тип жилья / этажность ────────────────────────────────────

_BUILDING_MAP = {
    "bt_new": "новостройка",
    "bt_old": "вторичка",
    "bt_1floor": "1 этаж",
    "bt_2floor": "2+ этажа",
}


@router.callback_query(CalcStates.choose_building_type, F.data.in_(set(_BUILDING_MAP)))
async def cb_building_type(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(building_type=_BUILDING_MAP[call.data])
    await state.set_state(CalcStates.enter_area)
    await call.message.edit_text(
        "📐 <b>Укажите площадь объекта (кв.м):</b>\n"
        "<i>Например: 60</i>",
        parse_mode="HTML",
    )


# ── Площадь ──────────────────────────────────────────────────

@router.message(CalcStates.enter_area)
async def msg_area(message: Message, state: FSMContext) -> None:
    value = validate_positive_number(message.text or "")
    if value is None or value < 5 or value > 2000:
        await message.answer("⚠️ Введите корректную площадь от 5 до 2000 кв.м:")
        return
    await state.update_data(area=value)
    await state.set_state(CalcStates.enter_rooms)
    await message.answer(
        "🚪 <b>Сколько комнат?</b>",
        reply_markup=rooms_kb,
        parse_mode="HTML",
    )


# ── Комнаты ───────────────────────────────────────────────────

@router.callback_query(CalcStates.enter_rooms, F.data.startswith("rooms_"))
async def cb_rooms(call: CallbackQuery, state: FSMContext) -> None:
    val = call.data.replace("rooms_", "").replace("plus", "+")
    rooms_int = 5 if val == "5+" else int(val)
    await state.update_data(rooms=rooms_int)
    await state.set_state(CalcStates.choose_wall_material)
    await call.message.edit_text(
        "🧱 <b>Материал стен:</b>",
        reply_markup=wall_kb,
        parse_mode="HTML",
    )


# ── Материал стен ─────────────────────────────────────────────

_WALL_MAP = {
    "wall_concrete": "Бетон",
    "wall_brick": "Кирпич",
    "wall_gas": "Газоблок/пеноблок",
    "wall_wood": "Дерево",
    "wall_other": "Другое",
}


@router.callback_query(CalcStates.choose_wall_material, F.data.in_(set(_WALL_MAP)))
async def cb_wall(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(wall_material=_WALL_MAP[call.data])
    await state.set_state(CalcStates.enter_sockets)
    await call.message.edit_text(
        "🔌 <b>Количество розеток</b> (всего по объекту):\n"
        "<i>Включая двойные — считайте каждое гнездо отдельно</i>",
        parse_mode="HTML",
    )


# ── Помощник для числовых вопросов ───────────────────────────

async def _ask_int(
    message: Message,
    state: FSMContext,
    key: str,
    next_state,
    next_prompt: str,
    reply_markup=None,
) -> None:
    value = validate_positive_integer(message.text or "")
    if value is None:
        await message.answer("⚠️ Введите целое число ≥ 0:")
        return
    await state.update_data(**{key: value})
    await state.set_state(next_state)
    await message.answer(next_prompt, reply_markup=reply_markup, parse_mode="HTML")


# ── Основные электрические точки ─────────────────────────────

@router.message(CalcStates.enter_sockets)
async def msg_sockets(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "sockets", CalcStates.enter_switches,
        "🔘 <b>Количество выключателей</b> (одноклавишные + двухклавишные):",
    )


@router.message(CalcStates.enter_switches)
async def msg_switches(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "switches", CalcStates.enter_spots,
        "💡 <b>Количество точечных светильников (споты):</b>\n"
        "<i>Встраиваемые в потолок точечные светильники</i>",
    )


@router.message(CalcStates.enter_spots)
async def msg_spots(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "spots", CalcStates.enter_lamps_simple,
        "🔆 <b>Количество люстр простых</b> (до 3 рожков, стандартная высота потолков):",
    )


@router.message(CalcStates.enter_lamps_simple)
async def msg_lamps_simple(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "lamps_simple", CalcStates.enter_lamps_hard,
        "✨ <b>Количество люстр сложных</b> (4+ рожков, высокие потолки, каскадные):",
    )


@router.message(CalcStates.enter_lamps_hard)
async def msg_lamps_hard(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "lamps_hard", CalcStates.enter_stove,
        "🍳 <b>Варочная панель</b> — сколько штук? (0 если нет)",
    )


# ── Дополнительные потребители ────────────────────────────────

@router.message(CalcStates.enter_stove)
async def msg_stove(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "stove", CalcStates.enter_oven,
        "🔥 <b>Духовой шкаф</b> — сколько штук? (0 если нет)",
    )


@router.message(CalcStates.enter_oven)
async def msg_oven(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "oven", CalcStates.enter_ac,
        "❄️ <b>Кондиционеры</b> — сколько штук? (0 если нет)",
    )


@router.message(CalcStates.enter_ac)
async def msg_ac(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "ac", CalcStates.enter_boiler,
        "🚿 <b>Нужно ли подключить бойлер/водонагреватель?</b>",
        reply_markup=yes_no_kb,
    )


@router.callback_query(CalcStates.enter_boiler, F.data.in_({"yn_yes", "yn_no"}))
async def cb_boiler(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(boiler=(call.data == "yn_yes"))
    await state.set_state(CalcStates.enter_floor_heating)
    await call.message.edit_text(
        "🌡 <b>Тёплые полы</b> — укажите площадь в кв.м (0 если не нужно):\n"
        "<i>Электрический тёплый пол под плитку или ламинат</i>",
        parse_mode="HTML",
    )


@router.message(CalcStates.enter_floor_heating)
async def msg_floor_heating(message: Message, state: FSMContext) -> None:
    value = validate_positive_number(message.text or "")
    if value is None:
        await message.answer("⚠️ Введите число кв.м ≥ 0:")
        return
    await state.update_data(floor_heating=value)
    await state.set_state(CalcStates.enter_washing_machine)
    await message.answer(
        "🫧 <b>Стиральная машина</b> — сколько штук? (0 если нет)",
        parse_mode="HTML",
    )


@router.message(CalcStates.enter_washing_machine)
async def msg_washing(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "washing_machine", CalcStates.enter_dishwasher,
        "🍽 <b>Посудомоечная машина</b> — сколько штук? (0 если нет)",
    )


@router.message(CalcStates.enter_dishwasher)
async def msg_dishwasher(message: Message, state: FSMContext) -> None:
    await _ask_int(
        message, state, "dishwasher", CalcStates.ask_shield,
        "⚡ <b>Нужна ли сборка/монтаж электрощита?</b>\n"
        "<i>Установка или замена распределительного щитка с автоматами</i>",
        reply_markup=yes_no_kb,
    )


# ── Дополнительные работы ─────────────────────────────────────

@router.callback_query(CalcStates.ask_shield, F.data.in_({"yn_yes", "yn_no"}))
async def cb_shield(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(shield_needed=(call.data == "yn_yes"))
    await state.set_state(CalcStates.ask_low_voltage)
    await call.message.edit_text(
        "📡 <b>Нужна ли слаботочка?</b>\n"
        "<i>Интернет, ТВ, видеонаблюдение</i>",
        reply_markup=yes_no_kb,
        parse_mode="HTML",
    )


@router.callback_query(CalcStates.ask_low_voltage, F.data.in_({"yn_yes", "yn_no"}))
async def cb_low_voltage(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(low_voltage=(call.data == "yn_yes"))
    await state.set_state(CalcStates.ask_demolition)
    await call.message.edit_text(
        "🔨 <b>Есть ли старые линии для демонтажа?</b>",
        reply_markup=yes_no_kb,
        parse_mode="HTML",
    )


@router.callback_query(CalcStates.ask_demolition, F.data.in_({"yn_yes", "yn_no"}))
async def cb_demolition(call: CallbackQuery, state: FSMContext) -> None:
    if call.data == "yn_yes":
        await state.set_state(CalcStates.enter_demolition_count)
        await call.message.edit_text(
            "🔨 <b>Сколько точек нужно демонтировать?</b>\n"
            "<i>Примерное количество розеток, выключателей и светильников под демонтаж</i>",
            parse_mode="HTML",
        )
    else:
        await state.update_data(demolition=0)
        await _go_to_contacts(call.message, state)


@router.message(CalcStates.enter_demolition_count)
async def msg_demolition_count(message: Message, state: FSMContext) -> None:
    value = validate_positive_integer(message.text or "")
    if value is None:
        await message.answer("⚠️ Введите целое число ≥ 0:")
        return
    await state.update_data(demolition=value)
    await _go_to_contacts(message, state)


async def _go_to_contacts(msg_or_message, state: FSMContext) -> None:
    await state.set_state(CalcStates.enter_name)
    if hasattr(msg_or_message, "answer"):
        await msg_or_message.answer(
            "👤 <b>Введите ваше имя:</b>",
            parse_mode="HTML",
        )
    else:
        await msg_or_message.edit_text(
            "👤 <b>Введите ваше имя:</b>",
            parse_mode="HTML",
        )


# ── Контакты ──────────────────────────────────────────────────

@router.message(CalcStates.enter_name)
async def msg_name(message: Message, state: FSMContext) -> None:
    name = sanitize_text(message.text or "", max_length=100)
    if len(name) < 2:
        await message.answer("⚠️ Введите имя (минимум 2 символа):")
        return
    await state.update_data(client_name=name)
    await state.set_state(CalcStates.enter_phone)
    await message.answer(
        "📞 <b>Ваш номер телефона:</b>\n"
        "<i>Например: 89181234567 или +7 918 123-45-67</i>",
        parse_mode="HTML",
    )


@router.message(CalcStates.enter_phone)
async def msg_phone(message: Message, state: FSMContext) -> None:
    phone = validate_phone(message.text or "")
    if phone is None:
        await message.answer(
            "⚠️ Не удалось распознать номер. "
            "Введите российский номер, например: <code>89181234567</code>",
            parse_mode="HTML",
        )
        return
    await state.update_data(client_phone=phone)
    await state.set_state(CalcStates.choose_contact_method)
    await message.answer(
        "💬 <b>Удобный способ связи:</b>",
        reply_markup=contact_kb,
        parse_mode="HTML",
    )


_CONTACT_MAP = {
    "contact_call": "Звонок",
    "contact_wa": "WhatsApp",
    "contact_tg": "Telegram",
}


@router.callback_query(CalcStates.choose_contact_method, F.data.in_(set(_CONTACT_MAP)))
async def cb_contact_method(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(contact_method=_CONTACT_MAP[call.data])
    # Передаём управление хендлеру подтверждения
    from handlers.user.confirm import show_confirmation
    await show_confirmation(call.message, state, call.from_user)
