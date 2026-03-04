"""Обработчики /start, /help, /cancel."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards import start_kb

router = Router(name="start")
log = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 <b>Добро пожаловать!</b>\n\n"
    "Я помогу рассчитать <b>примерную стоимость</b> электромонтажных работ "
    "в вашей квартире или доме в Ростове-на-Дону.\n\n"
    "ℹ️ Расчёт является предварительным. "
    "Точная смета составляется после выезда специалиста или по вашему проекту. "
    "<b>Осмотр объекта — бесплатно.</b>\n\n"
    "Нажмите кнопку ниже, чтобы начать:"
)

HELP_TEXT = (
    "🔧 <b>Как пользоваться ботом:</b>\n\n"
    "1. Нажмите «Рассчитать стоимость работ»\n"
    "2. Ответьте на вопросы о вашем объекте\n"
    "3. Получите примерную стоимость\n"
    "4. Отправьте заявку мастеру\n\n"
    "<b>Команды:</b>\n"
    "/start — главное меню\n"
    "/cancel — отмена и возврат в главное меню\n"
    "/help — эта справка\n"
)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Приветственное сообщение и кнопка запуска калькулятора."""
    await state.clear()
    log.info("User %s started bot", message.from_user.id)
    await message.answer(WELCOME_TEXT, reply_markup=start_kb, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current:
        await message.answer(
            "❌ Опрос отменён. Возвращаемся в главное меню.",
            reply_markup=start_kb,
        )
    else:
        await message.answer("Главное меню:", reply_markup=start_kb)
