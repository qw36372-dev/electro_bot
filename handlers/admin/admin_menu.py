"""Административная панель: главное меню и просмотр настроек."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from database.crud import get_all_settings, get_stats
from keyboards import admin_menu_kb
from utils.formatters import format_all_settings

router = Router(name="admin_menu")
log = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    await state.clear()
    log.info("Admin %s opened admin panel", message.from_user.id)
    await message.answer(
        "🔑 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_back")
async def cb_adm_back(call: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        "🔑 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm_view")
async def cb_adm_view(call: CallbackQuery) -> None:
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    settings = await get_all_settings()
    text = format_all_settings(settings)
    from keyboards import kb
    back_kb = kb([("⬅️ Назад", "adm_back")])
    await call.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")


@router.callback_query(F.data == "adm_stats")
async def cb_adm_stats(call: CallbackQuery) -> None:
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    stats = await get_stats()
    text = (
        "📊 <b>Статистика заявок</b>\n\n"
        f"Всего заявок: <b>{stats['total']}</b>\n"
        f"Сегодня: <b>{stats['today']}</b>\n"
        f"За неделю: <b>{stats['week']}</b>\n"
        f"За месяц: <b>{stats['month']}</b>\n\n"
        f"Средняя стоимость расчёта: <b>{stats['avg_price']:,} ₽</b>\n\n".replace(",", "\u00a0")
        + f"Квартиры: {stats['apt_count']}\n"
        f"Дома: {stats['house_count']}"
    )
    from keyboards import kb
    back_kb = kb([("⬅️ Назад", "adm_back")])
    await call.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")
