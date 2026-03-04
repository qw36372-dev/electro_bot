"""Административное управление коэффициентами."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS, COEFF_LABELS
from database.crud import get_all_settings, set_setting
from keyboards import coeffs_kb
from states import AdminStates
from utils.validators import validate_positive_number

router = Router(name="admin_coeffs")
log = logging.getLogger(__name__)


@router.callback_query(F.data == "adm_coeffs")
async def cb_adm_coeffs(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.choose_coeff_item)
    settings = await get_all_settings()
    await call.message.edit_text(
        "📐 <b>Управление коэффициентами</b>\n\nВыберите параметр:",
        reply_markup=coeffs_kb(settings),
        parse_mode="HTML",
    )


@router.callback_query(AdminStates.choose_coeff_item, F.data.startswith("edit_coeff_"))
async def cb_choose_coeff(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    key = call.data.replace("edit_coeff_", "")
    label = COEFF_LABELS.get(key, key)
    settings = await get_all_settings()
    current = settings.get(key, 0)

    await state.update_data(editing_key=key)
    await state.set_state(AdminStates.enter_new_coeff)
    await call.message.edit_text(
        f"📐 <b>{label}</b>\n\n"
        f"Текущее значение: <b>{current}</b>\n\n"
        "Введите новое значение:\n"
        "<i>Для коэффициентов умножения — например 1.15 означает +15%.\n"
        "Для разброса — например 0.10 означает ±10%.</i>",
        parse_mode="HTML",
    )


@router.message(AdminStates.enter_new_coeff)
async def msg_new_coeff(message: Message, state: FSMContext) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    value = validate_positive_number(message.text or "")
    if value is None or value <= 0:
        await message.answer("⚠️ Введите корректное положительное число (например 1.15 или 0.10):")
        return

    data = await state.get_data()
    key = data.get("editing_key")
    label = COEFF_LABELS.get(key, key)

    await set_setting(key, value)
    log.info("Admin %s updated %s = %s", message.from_user.id, key, value)

    await state.set_state(AdminStates.choose_coeff_item)
    settings = await get_all_settings()
    await message.answer(
        f"✅ «{label}» обновлён: <b>{value}</b>",
        parse_mode="HTML",
    )
    await message.answer(
        "📐 <b>Управление коэффициентами</b>\n\nВыберите параметр:",
        reply_markup=coeffs_kb(settings),
        parse_mode="HTML",
    )
