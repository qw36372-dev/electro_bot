"""CRUD-операции: получение/обновление настроек, создание заявок, статистика."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DATABASE_URL, DEFAULT_COEFFICIENTS, DEFAULT_PRICES
from database.models import Base, Lead, Setting


# ── Движок и фабрика сессий ──────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False)
SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def init_db() -> None:
    """Создаёт таблицы и заполняет настройки дефолтными значениями."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionFactory() as session:
        all_defaults = {**DEFAULT_PRICES, **DEFAULT_COEFFICIENTS}
        for key, value in all_defaults.items():
            existing = await session.scalar(select(Setting).where(Setting.key == key))
            if existing is None:
                session.add(Setting(key=key, value=value))
        await session.commit()


# ── Настройки ────────────────────────────────────────────────

async def get_setting(key: str) -> float:
    """Возвращает значение настройки по ключу."""
    async with SessionFactory() as session:
        row = await session.scalar(select(Setting).where(Setting.key == key))
        if row is None:
            all_defaults = {**DEFAULT_PRICES, **DEFAULT_COEFFICIENTS}
            return all_defaults.get(key, 0.0)
        return row.value


async def set_setting(key: str, value: float) -> None:
    """Обновляет или создаёт настройку."""
    async with SessionFactory() as session:
        row = await session.scalar(select(Setting).where(Setting.key == key))
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            session.add(Setting(key=key, value=value))
        await session.commit()


async def get_all_settings() -> dict[str, float]:
    """Возвращает все настройки одним словарём."""
    async with SessionFactory() as session:
        rows = (await session.scalars(select(Setting))).all()
        return {r.key: r.value for r in rows}


# ── Заявки ────────────────────────────────────────────────────

async def create_lead(data: dict) -> Lead:
    """Сохраняет заявку в базу и возвращает объект с ID."""
    async with SessionFactory() as session:
        lead = Lead(**data)
        session.add(lead)
        await session.commit()
        await session.refresh(lead)
        return lead


async def get_last_lead_time(user_id: int) -> datetime | None:
    """Возвращает время последней заявки пользователя."""
    async with SessionFactory() as session:
        row = await session.scalar(
            select(Lead)
            .where(Lead.user_id == user_id)
            .order_by(Lead.created_at.desc())
            .limit(1)
        )
        return row.created_at if row else None


# ── Статистика ────────────────────────────────────────────────

async def get_stats() -> dict:
    """Возвращает агрегированную статистику по заявкам."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    async with SessionFactory() as session:
        total = await session.scalar(select(func.count(Lead.id)))
        today = await session.scalar(
            select(func.count(Lead.id)).where(Lead.created_at >= today_start)
        )
        week = await session.scalar(
            select(func.count(Lead.id)).where(Lead.created_at >= week_start)
        )
        month = await session.scalar(
            select(func.count(Lead.id)).where(Lead.created_at >= month_start)
        )
        avg_price = await session.scalar(
            select(func.avg((Lead.price_min + Lead.price_max) / 2))
        )

        apt_count = await session.scalar(
            select(func.count(Lead.id)).where(Lead.object_type == "квартира")
        )
        house_count = await session.scalar(
            select(func.count(Lead.id)).where(Lead.object_type == "дом")
        )

    return {
        "total": total or 0,
        "today": today or 0,
        "week": week or 0,
        "month": month or 0,
        "avg_price": int(avg_price) if avg_price else 0,
        "apt_count": apt_count or 0,
        "house_count": house_count or 0,
    }
