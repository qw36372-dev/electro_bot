"""Административное управление ценами."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS, PRICE_LABELS
from database.crud import get_all_settings, set_setting
from keyboards import prices_kb
from states import AdminStates
from utils.validators import validate_positive_number

router = Router(name="admin_prices")
log = logging.getLogger(__name__)


@router.callback_query(F.data == "adm_prices")
async def cb_adm_prices(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.choose_price_item)
    settings = await get_all_settings()
    await call.message.edit_text(
        "💰 <b>Управление ценами</b>\n\nВыберите позицию для редактирования:",
        reply_markup=prices_kb(settings),
        parse_mode="HTML",
    )


@router.callback_query(AdminStates.choose_price_item, F.data.startswith("edit_price_"))
async def cb_choose_price(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    key = call.data.replace("edit_price_", "")
    label = PRICE_LABELS.get(key, key)
    settings = await get_all_settings()
    current = int(settings.get(key, 0))

    await state.update_data(editing_key=key)
    await state.set_state(AdminStates.enter_new_price)
    await call.message.edit_text(
        f"💰 <b>{label}</b>\n\n"
        f"Текущая цена: <b>{current} ₽</b>\n\n"
        "Введите новую цену (₽):",
        parse_mode="HTML",
    )


@router.message(AdminStates.enter_new_price)
async def msg_new_price(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    value = validate_positive_number(message.text or "")
    if value is None or value <= 0:
        await message.answer("⚠️ Введите корректную цену > 0:")
        return

    data = await state.get_data()
    key = data.get("editing_key")
    label = PRICE_LABELS.get(key, key)

    await set_setting(key, value)
    log.info("Admin %s updated %s = %s", message.from_user.id, key, value)

    await state.set_state(AdminStates.choose_price_item)
    settings = await get_all_settings()
    await message.answer(
        f"✅ Цена «{label}» обновлена: <b>{int(value)} ₽</b>",
        parse_mode="HTML",
    )
    await message.answer(
        "💰 <b>Управление ценами</b>\n\nВыберите позицию:",
        reply_markup=prices_kb(settings),
        parse_mode="HTML",
    )
