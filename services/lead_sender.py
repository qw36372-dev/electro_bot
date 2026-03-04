"""Отправка заявки в приватный Telegram-канал."""

from aiogram import Bot

from config import LEADS_CHANNEL_ID
from database.models import Lead
from utils.formatters import format_lead_message


async def send_lead_to_channel(bot: Bot, lead: Lead) -> bool:
    """
    Отправляет структурированное сообщение с заявкой в канал.

    :returns: True если успешно, False при ошибке
    """
    if not LEADS_CHANNEL_ID:
        return False

    text = format_lead_message(lead)
    try:
        await bot.send_message(
            chat_id=LEADS_CHANNEL_ID,
            text=text,
            parse_mode="HTML",
        )
        return True
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Ошибка отправки заявки: %s", exc)
        return False
