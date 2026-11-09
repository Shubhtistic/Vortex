from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.vortex.infrastructure.config import get_settings

# --- settings ---
settings = get_settings()


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


# --- transaction context ---
@asynccontextmanager
# actual uow
async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Open one session and transaction for an application operation."""
    async with SessionFactory() as db_session:
        async with db_session.begin():
            yield db_session
