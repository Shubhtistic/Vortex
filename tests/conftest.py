import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient # For unified async loop
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.db.session import get_session
from app.core.config import settings
from app.core.celery_app import celery_app

# async engine
async_engine = create_async_engine(settings.TEST_POSTGRES_URL, echo=True)

# this gives multiple sessions to use
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

#Database Fixture (Setup & Teardown)
@pytest_asyncio.fixture(name="session")
async def session_fixture():
    # STEP1 -> Arrange: Build tables
    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

    # STEP 2-> Act: Hand over the session
    async with AsyncSessionLocal() as session:
        yield session

    # Step 3 -> Teardown Tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

# Async Client Fixture
@pytest_asyncio.fixture(name="client")
async def client_fixture(session: AsyncSession):
    # override the database dependency
    async def override_get_session():
        yield session
    app.dependency_overrides[get_session] = override_get_session

    # Configure Celery for immediate execution
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    # Use AsyncClient to prevent loop conflicts
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # Cleanup after test
    app.dependency_overrides.clear()
    celery_app.conf.task_always_eager = False