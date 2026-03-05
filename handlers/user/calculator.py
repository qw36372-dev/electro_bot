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
    outdoor_kb_multi,
    rooms_kb,
    skip_extra_kb,
    wall_kb_multi,
    yes_no_kb,
    WALL_KEY_TO_LABEL,
    OUTDOOR_KEY_TO_LABEL,
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

EXTRA_INFO_TEXT = (
    "<b>Дополнительные сведения мастеру</b>\n\n"
    "Здесь вы можете описать свои пожелания, другие условия работы "
    "или любую информацию, которую не удалось указать в опросе.\n\n"
    "<i>Данные не влияют на предварительный расчёт, но будут полезны мастеру.</i>\n\n"
    "Для пропуска нажмите <b>НЕТ</b>"
)


# ── Хелперы управления сообщениями ───────────────────────────

async def _edit(call_msg, state: FSMContext, text: str, reply_markup=None) -> None:
    await call_msg.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.update_data(last_bot_msg_id=call_msg.message_id)


async def _next_q(message: Message, state: FSMContext, text: str, reply_markup=None) -> None:
    data = await state.get_data()
    last_id = data.get("last_bot_msg_id")
    try:
        await message.delete()
    except Exception:
        pass
    if last_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass
    msg = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.update_data(last_bot_msg_id=msg.message_id)


async def _invalid(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass


# ── Запуск калькулятора ──────────────────────────────────────

@router.callback_query(F.data == "calc_start")
async def cb_calc_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CalcStates.enter_city)
    await _edit(call.message, state,
        "<b>Из какого вы города?</b>\n<i>Введите название города</i>",
    )


# ── Город ────────────────────────────────────────────────────

@router.message(CalcStates.enter_city)
async def msg_city(message: Message, state: FSMContext) -> None:
    city = sanitize_text(message.text or "", max_length=100)
    if len(city) < 2:
        await _invalid(message)
        return
    await state.update_data(city=city)
    await state.set_state(CalcStates.enter_district)
    await _next_q(message, state,
        "<b>Какой район или ЖК?</b>\n<i>Введите район или название жилого комплекса</i>",
    )


# ── Район / ЖК ───────────────────────────────────────────────

@router.message(CalcStates.enter_district)
async def msg_district(message: Message, state: FSMContext) -> None:
    district = sanitize_text(message.text or "", max_length=150)
    if len(district) < 2:
        await _invalid(message)
        return
    await state.update_data(district=district)
    await state.set_state(CalcStates.choose_object_type)
    await _next_q(message, state,
        "<b>Выберите тип объекта:</b>",
        reply_markup=object_type_kb,
    )


# ── Тип объекта ──────────────────────────────────────────────

@router.callback_query(CalcStates.choose_object_type, F.data.in_({"obj_flat", "obj_house"}))
async def cb_object_type(call: CallbackQuery, state: FSMContext) -> None:
    is_flat = call.data == "obj_flat"
    await state.update_data(object_type="квартира" if is_flat else "дом")
    await state.set_state(CalcStates.choose_building_type)
    if is_flat:
        await _edit(call.message, state,
            "<b>Тип жилья:</b>",
            reply_markup=building_type_flat_kb,
        )
    else:
        await _edit(call.message, state,
            "<b>Количество этажей:</b>",
            reply_markup=building_type_house_kb,
        )


# ── Тип жилья / этажность ────────────────────────────────────

_BUILDING_MAP = {
    "bt_new":    "новостройка",
    "bt_old":    "вторичка",
    "bt_1floor": "1 этаж",
    "bt_2floor": "2+ этажа",
}


@router.callback_query(CalcStates.choose_building_type, F.data.in_(set(_BUILDING_MAP)))
async def cb_building_type(call: CallbackQuery, state: FSMContext) -> None:
    building = _BUILDING_MAP[call.data]
    await state.update_data(building_type=building)
    data = await state.get_data()
    if data.get("object_type") == "дом":
        await state.set_state(CalcStates.ask_outdoor_work)
        await _edit(call.message, state,
            "<b>Нужны ли дополнительные электромонтажные работы на участке?</b>",
            reply_markup=yes_no_kb,
        )
    else:
        await state.set_state(CalcStates.enter_area)
        await _edit(call.message, state,
            "<b>Укажите площадь объекта (кв.м):</b>\n<i>Например: 60</i>",
        )


# ── Работы на участке (только для дома) ──────────────────────

@router.callback_query(CalcStates.ask_outdoor_work, F.data.in_({"yn_yes", "yn_no"}))
async def cb_ask_outdoor(call: CallbackQuery, state: FSMContext) -> None:
    if call.data == "yn_yes":
        await state.update_data(outdoor_selection=[])
        await state.set_state(CalcStates.choose_outdoor_types)
        await _edit(call.message, state,
            "<b>Выберите объекты на участке:</b>\n"
            "<i>Можно выбрать несколько, затем нажмите Далее</i>",
            reply_markup=outdoor_kb_multi([]),
        )
    else:
        await state.update_data(outdoor_work="Нет")
        await state.set_state(CalcStates.enter_area)
        await _edit(call.message, state,
            "<b>Укажите площадь дома (кв.м):</b>\n<i>Например: 120</i>",
        )


@router.callback_query(CalcStates.choose_outdoor_types, F.data.startswith("outdoor_toggle_"))
async def cb_outdoor_toggle(call: CallbackQuery, state: FSMContext) -> None:
    key = call.data.replace("outdoor_toggle_", "")
    label = OUTDOOR_KEY_TO_LABEL.get(key, key)
    data = await state.get_data()
    selected: list = list(data.get("outdoor_selection", []))
    if label in selected:
        selected.remove(label)
    else:
        selected.append(label)
    await state.update_data(outdoor_selection=selected)
    await call.message.edit_reply_markup(reply_markup=outdoor_kb_multi(selected))
    await call.answer()


@router.callback_query(CalcStates.choose_outdoor_types, F.data == "outdoor_done")
async def cb_outdoor_done(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected: list = data.get("outdoor_selection", [])
    if not selected:
        await call.answer("Выберите хотя бы один вариант", show_alert=True)
        return
    await state.update_data(outdoor_work=", ".join(selected))
    await state.set_state(CalcStates.enter_area)
    await _edit(call.message, state,
        "<b>Укажите площадь дома (кв.м):</b>\n<i>Например: 120</i>",
    )


# ── Площадь ──────────────────────────────────────────────────

@router.message(CalcStates.enter_area)
async def msg_area(message: Message, state: FSMContext) -> None:
    value = validate_positive_number(message.text or "")
    if value is None or value < 5 or value > 2000:
        await _invalid(message)
        return
    await state.update_data(area=value)
    await state.set_state(CalcStates.enter_rooms)
    await _next_q(message, state, "<b>Сколько комнат?</b>", reply_markup=rooms_kb)


# ── Комнаты ───────────────────────────────────────────────────

_ROOMS_MAP = {
    "rooms_studio": 0,
    "rooms_1":      1,
    "rooms_2":      2,
    "rooms_3":      3,
    "rooms_4plus":  4,
}


@router.callback_query(CalcStates.enter_rooms, F.data.in_(set(_ROOMS_MAP)))
async def cb_rooms(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(rooms=_ROOMS_MAP[call.data], wall_selection=[])
    await state.set_state(CalcStates.choose_wall_material)
    await _edit(call.message, state,
        "<b>Материал стен:</b>\n<i>Можно выбрать несколько вариантов, затем нажмите Далее</i>",
        reply_markup=wall_kb_multi([]),
    )


# ── Материал стен (множественный выбор) ──────────────────────

@router.callback_query(CalcStates.choose_wall_material, F.data.startswith("wall_toggle_"))
async def cb_wall_toggle(call: CallbackQuery, state: FSMContext) -> None:
    key = call.data.replace("wall_toggle_", "")
    label = WALL_KEY_TO_LABEL.get(key, key)
    data = await state.get_data()
    selected: list = list(data.get("wall_selection", []))
    if label in selected:
        selected.remove(label)
    else:
        selected.append(label)
    await state.update_data(wall_selection=selected)
    await call.message.edit_reply_markup(reply_markup=wall_kb_multi(selected))
    await call.answer()


@router.callback_query(CalcStates.choose_wall_material, F.data == "wall_done")
async def cb_wall_done(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected: list = data.get("wall_selection", [])
    if not selected:
        await call.answer("Выберите хотя бы один вариант", show_alert=True)
        return
    await state.update_data(wall_material=", ".join(selected))
    await state.set_state(CalcStates.enter_sockets)
    await _edit(call.message, state,
        "<b>Количество розеток</b> (всего по объекту):\n"
        "<i>Включая двойные — считайте каждое гнездо отдельно</i>",
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
        await _invalid(message)
        return
    await state.update_data(**{key: value})
    await state.set_state(next_state)
    await _next_q(message, state, next_prompt, reply_markup=reply_markup)


# ── Основные электрические точки ─────────────────────────────

@router.message(CalcStates.enter_sockets)
async def msg_sockets(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "sockets", CalcStates.enter_switches,
        "<b>Количество выключателей</b> (одноклавишные + двухклавишные):",
    )


@router.message(CalcStates.enter_switches)
async def msg_switches(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "switches", CalcStates.enter_spots,
        "<b>Количество точечных светильников (споты):</b>\n"
        "<i>Встраиваемые в потолок точечные светильники</i>",
    )


@router.message(CalcStates.enter_spots)
async def msg_spots(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "spots", CalcStates.enter_lamps_simple,
        "<b>Количество люстр простых</b> (до 3 рожков, стандартная высота потолков):",
    )


@router.message(CalcStates.enter_lamps_simple)
async def msg_lamps_simple(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "lamps_simple", CalcStates.enter_lamps_hard,
        "<b>Количество люстр сложных</b> (4+ рожков, высокие потолки, каскадные):",
    )


@router.message(CalcStates.enter_lamps_hard)
async def msg_lamps_hard(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "lamps_hard", CalcStates.enter_stove,
        "<b>Варочная панель</b> — сколько штук? (0 если нет)",
    )


# ── Дополнительные потребители ────────────────────────────────

@router.message(CalcStates.enter_stove)
async def msg_stove(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "stove", CalcStates.enter_oven,
        "<b>Духовой шкаф</b> — сколько штук? (0 если нет)",
    )


@router.message(CalcStates.enter_oven)
async def msg_oven(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "oven", CalcStates.enter_ac,
        "<b>Кондиционеры</b> — сколько штук? (0 если нет)",
    )


@router.message(CalcStates.enter_ac)
async def msg_ac(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "ac", CalcStates.enter_floor_heating,
        "<b>Тёплые полы</b> — укажите площадь в кв.м (0 если не нужно):\n"
        "<i>Электрический тёплый пол под плитку или ламинат</i>",
    )


@router.message(CalcStates.enter_floor_heating)
async def msg_floor_heating(message: Message, state: FSMContext) -> None:
    value = validate_positive_number(message.text or "")
    if value is None:
        await _invalid(message)
        return
    await state.update_data(floor_heating=value)
    await state.set_state(CalcStates.enter_washing_machine)
    await _next_q(message, state, "<b>Стиральная машина</b> — сколько штук? (0 если нет)")


@router.message(CalcStates.enter_washing_machine)
async def msg_washing(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "washing_machine", CalcStates.enter_dishwasher,
        "<b>Посудомоечная машина</b> — сколько штук? (0 если нет)",
    )


@router.message(CalcStates.enter_dishwasher)
async def msg_dishwasher(message: Message, state: FSMContext) -> None:
    await _ask_int(message, state, "dishwasher", CalcStates.enter_boiler,
        "<b>Нужно ли подключить бойлер/водонагреватель?</b>",
        reply_markup=yes_no_kb,
    )


# ── Блок да/нет ──────────────────────────────────────────────

@router.callback_query(CalcStates.enter_boiler, F.data.in_({"yn_yes", "yn_no"}))
async def cb_boiler(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(boiler=(call.data == "yn_yes"))
    await state.set_state(CalcStates.ask_shield)
    await _edit(call.message, state,
        "<b>Нужна ли сборка/монтаж электрощита?</b>\n"
        "<i>Установка или замена распределительного щитка с автоматами</i>",
        reply_markup=yes_no_kb,
    )


@router.callback_query(CalcStates.ask_shield, F.data.in_({"yn_yes", "yn_no"}))
async def cb_shield(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(shield_needed=(call.data == "yn_yes"))
    await state.set_state(CalcStates.ask_low_voltage)
    await _edit(call.message, state,
        "<b>Нужна ли слаботочка?</b>\n<i>Интернет, ТВ, видеонаблюдение</i>",
        reply_markup=yes_no_kb,
    )


@router.callback_query(CalcStates.ask_low_voltage, F.data.in_({"yn_yes", "yn_no"}))
async def cb_low_voltage(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(low_voltage=(call.data == "yn_yes"))
    await state.set_state(CalcStates.ask_demolition)
    await _edit(call.message, state,
        "<b>Есть ли старые линии для демонтажа?</b>",
        reply_markup=yes_no_kb,
    )


@router.callback_query(CalcStates.ask_demolition, F.data.in_({"yn_yes", "yn_no"}))
async def cb_demolition(call: CallbackQuery, state: FSMContext) -> None:
    if call.data == "yn_yes":
        await state.set_state(CalcStates.enter_demolition_count)
        await _edit(call.message, state,
            "<b>Сколько точек нужно демонтировать?</b>\n"
            "<i>Примерное количество розеток, выключателей и светильников</i>",
        )
    else:
        await state.update_data(demolition=0)
        await state.set_state(CalcStates.enter_extra_info)
        await _edit(call.message, state, EXTRA_INFO_TEXT, reply_markup=skip_extra_kb)


@router.message(CalcStates.enter_demolition_count)
async def msg_demolition_count(message: Message, state: FSMContext) -> None:
    value = validate_positive_integer(message.text or "")
    if value is None:
        await _invalid(message)
        return
    await state.update_data(demolition=value)
    await state.set_state(CalcStates.enter_extra_info)
    await _next_q(message, state, EXTRA_INFO_TEXT, reply_markup=skip_extra_kb)


# ── Дополнительные сведения мастеру ──────────────────────────

@router.callback_query(CalcStates.enter_extra_info, F.data == "extra_skip")
async def cb_extra_skip(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(extra_info="")
    await state.set_state(CalcStates.enter_name)
    await _edit(call.message, state, "<b>Введите ваше имя:</b>")


@router.message(CalcStates.enter_extra_info)
async def msg_extra_info(message: Message, state: FSMContext) -> None:
    text = sanitize_text(message.text or "", max_length=1000)
    if len(text) < 1:
        await _invalid(message)
        return
    await state.update_data(extra_info=text)
    await state.set_state(CalcStates.enter_name)
    await _next_q(message, state, "<b>Введите ваше имя:</b>")


# ── Контакты ──────────────────────────────────────────────────

@router.message(CalcStates.enter_name)
async def msg_name(message: Message, state: FSMContext) -> None:
    name = sanitize_text(message.text or "", max_length=100)
    if len(name) < 2:
        await _invalid(message)
        return
    await state.update_data(client_name=name)
    await state.set_state(CalcStates.enter_phone)
    await _next_q(message, state,
        "<b>Ваш номер телефона:</b>\n<i>Например: 89181234567 или +7 918 123-45-67</i>",
    )


@router.message(CalcStates.enter_phone)
async def msg_phone(message: Message, state: FSMContext) -> None:
    phone = validate_phone(message.text or "")
    if phone is None:
        await _invalid(message)
        return
    await state.update_data(client_phone=phone)
    await state.set_state(CalcStates.choose_contact_method)
    await _next_q(message, state, "<b>Удобный способ связи:</b>", reply_markup=contact_kb)


_CONTACT_MAP = {
    "contact_call": "Звонок",
    "contact_wa":   "WhatsApp",
    "contact_tg":   "Telegram",
}


@router.callback_query(CalcStates.choose_contact_method, F.data.in_(set(_CONTACT_MAP)))
async def cb_contact_method(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(contact_method=_CONTACT_MAP[call.data])
    from handlers.user.confirm import show_confirmation
    await show_confirmation(call.message, state, call.from_user)
