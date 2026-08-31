from typing import Annotated, TypeVar

from fastapi import Depends
from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from src.vortex.shared.config import get_settings

# --- settings ---
settings = get_settings()

# --- Typevar placeholder for SqlModel objects ---
Model = TypeVar("Model", bound=SQLModel)


# --- Engine ----
db_engine = create_async_engine(
    settings.postgres.postgres_async_url,
    echo=False,
    pool_size=10,
    max_overflow=10,
    pool_timeout=20,
    pool_recycle=1800,
    pool_pre_ping=True,
)


# --- session factory ----
SessionFactory = async_sessionmaker(
    bind=db_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- fastapi db dependancy ---
async def get_db_session():
    """Yield a request-scoped session; auto-rollback on unhandled exception."""
    async with SessionFactory() as db_session:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise


def get_session_factory():
    return SessionFactory


# --- Annotated Dep ---
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


# --- CRUD Utils ---


async def create(
    instance: Model,
    db_session: AsyncSession,
) -> Model:
    """Insert a new row. Flushes only — caller's transaction boundary commits."""
    db_session.add(instance)
    await db_session.flush()
    await db_session.refresh(instance)
    return instance


async def get_one(
    model: type[Model],
    pk: object,
    db_session: AsyncSession,
) -> Model | None:
    """Fetch a single row by primary key."""
    return await db_session.get(model, pk)


async def get_all(
    stmt: Select,
    db_session: AsyncSession,
) -> list[Model]:
    """Fetch all rows. Pass pre-built query statement from upper layer."""
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def delete_by_id(
    model: type[Model],
    pk: object,
    db_session: AsyncSession,
) -> bool:
    """Delete by primary key. Returns True if a row was actually deleted."""
    pk_col = list(model.__table__.primary_key.columns)[0]
    stmt = delete(model).where(pk_col == pk)

    result = await db_session.execute(stmt)
    return result.rowcount > 0


async def check_exists(
    model: type[Model],
    db_session: AsyncSession,
    filters: dict | None = None,
) -> bool:
    """Check if any row exists.  Uses SELECT 1 (portable across all RDBMS)."""
    stmt = select(1).select_from(model).limit(1)
    if filters:
        for key, value in filters.items():
            stmt = stmt.where(getattr(model, key) == value)

    result = await db_session.execute(stmt)
    return result.scalar() is not None


async def get_one_by_query(q: Select, db_session: AsyncSession):
    result = await db_session.execute(q)
    return result.scalar_one_or_none()


async def execute_query(
    query,
    db_session: AsyncSession,
):
    """caller must interpret the result
    one_or_none(), all(), scalar(), etc -> since the shape varies per query and this helper can't assume one
    """

    return await db_session.execute(query)
