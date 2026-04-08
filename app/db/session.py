# Engine-> The always-open connection pool to Postgres
# Session -> A temporary workspace for a single request, When a user asks for data, we open a session.
# When the request is done, we closw it

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings


engine = create_async_engine(settings.POSTGRES_URL, echo=True)
# echo = True -> o/p shown on our terminal


LocalAsyncSession = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session():
    async with LocalAsyncSession() as session:
        yield session  # yields an async db session for us to use

# by using the yield keyword this becomes a generator function
# This returns an async generator object
# which yields: session
# so we get an session object
