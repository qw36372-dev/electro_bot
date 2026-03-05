"""Подтверждение, отправка заявки и финальные действия."""

import logging
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from config import SPAM_INTERVAL
from database.crud import create_lead, get_last_lead_time
from keyboards import confirm_kb, start_kb
from services.lead_sender import send_lead_to_channel
from services.pricing import calculate_price
from states import CalcStates
from utils.formatters import format_summary

router = Router(name="confirm")
log = logging.getLogger(__name__)


async def show_confirmation(message: Message, state: FSMContext, user: User) -> None:
    """Считает стоимость и показывает итоговую сводку с кнопками подтверждения."""
    data = await state.get_data()

    price_min, price_max = await calculate_price(data)
    await state.update_data(price_min=price_min, price_max=price_max)

    text = format_summary(data, price_min, price_max)
    await state.set_state(CalcStates.confirm)

    try:
        await message.edit_text(text, reply_markup=confirm_kb, parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=confirm_kb, parse_mode="HTML")


@router.callback_query(CalcStates.confirm, F.data == "submit_lead")
async def cb_submit(call: CallbackQuery, state: FSMContext) -> None:
    """Антиспам + сохранение в БД + отправка в канал."""
    user = call.from_user

    # Антиспам
    last_time = await get_last_lead_time(user.id)
    if last_time:
        elapsed = (datetime.utcnow() - last_time).total_seconds()
        if elapsed < SPAM_INTERVAL:
            wait = int(SPAM_INTERVAL - elapsed)
            await call.answer(
                f"⏳ Следующую заявку можно отправить через {wait} сек.", show_alert=True
            )
            return

    data = await state.get_data()

    lead_data = {
        "user_id": user.id,
        "city": data.get("city"),
        "district": data.get("district"),
        "outdoor_work": data.get("outdoor_work", "Нет"),
        "username": user.username,
        "object_type": data.get("object_type"),
        "building_type": data.get("building_type"),
        "area": data.get("area"),
        "rooms": data.get("rooms"),
        "wall_material": data.get("wall_material"),
        "sockets": data.get("sockets", 0),
        "switches": data.get("switches", 0),
        "spots": data.get("spots", 0),
        "lamps_simple": data.get("lamps_simple", 0),
        "lamps_hard": data.get("lamps_hard", 0),
        "stove": data.get("stove", 0),
        "oven": data.get("oven", 0),
        "ac": data.get("ac", 0),
        "boiler": data.get("boiler", False),
        "floor_heating": data.get("floor_heating", 0.0),
        "washing_machine": data.get("washing_machine", 0),
        "dishwasher": data.get("dishwasher", 0),
        "shield_needed": data.get("shield_needed", False),
        "low_voltage": data.get("low_voltage", False),
        "demolition": data.get("demolition", 0),
        "price_min": data.get("price_min"),
        "price_max": data.get("price_max"),
        "extra_info": data.get("extra_info", ""),
        "client_name": data.get("client_name"),
        "client_phone": data.get("client_phone"),
        "contact_method": data.get("contact_method"),
    }

    lead = await create_lead(lead_data)
    log.info("New lead #%s from user %s", lead.id, user.id)

    # Отправка в канал
    await send_lead_to_channel(call.bot, lead)

    await state.clear()
    await call.message.edit_text(
        "✅ <b>Спасибо!</b> Ваша заявка отправлена.\n\n"
        "Мастер свяжется с вами в ближайшее время. 👍",
        parse_mode="HTML",
    )
    await call.message.answer("Главное меню:", reply_markup=start_kb)


@router.callback_query(CalcStates.confirm, F.data == "edit_data")
async def cb_edit(call: CallbackQuery, state: FSMContext) -> None:
    """Возврат к началу опроса с сохранением введённых данных в state."""
    await state.set_state(CalcStates.choose_object_type)
    from keyboards import object_type_kb
    await call.message.edit_text(
        "🔄 Давайте начнём заново.\n\n🏗 <b>Выберите тип объекта:</b>",
        reply_markup=object_type_kb,
        parse_mode="HTML",
    )


@router.callback_query(CalcStates.confirm, F.data == "cancel_lead")
async def cb_cancel_lead(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("❌ Заявка отменена.")
    await call.message.answer("Главное меню:", reply_markup=start_kb)
