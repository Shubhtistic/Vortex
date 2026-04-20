from contextlib import asynccontextmanager

from pytest import MonkeyPatch
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.db.db_models import SQLModel
from app.main import app
from app.core.redis import init_redis_pool,close_redis_pool

from app.db.session import get_session
from app.core.config import settings

async_engine=create_async_engine(settings.TEST_POSTGRES_URL, echo=True)

# fixture -> a piece of code that runs before our tests to give us all required tools
@pytest_asyncio.fixture(scope="session", autouse=True)
# scope = "session" -> only run this for first time, building table is slow
# autouse -> runs in background without us having to run it explicitly
# autouse -> run automatically when we type 'pytest'
async def setup_database():
    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
        # first lets build all table in the mock db
    yield # pause

    #  when test closes this runs
    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)
    await async_engine.dispose() # close all db connections



@pytest_asyncio.fixture(scope="session",autouse=True)
async def setup_redis():
    await init_redis_pool()
    yield
    await close_redis_pool()


@pytest_asyncio.fixture(name="session")
# name = "session" -> we can direcly this fixture inside our tests directly using its name
async def session_fixture():
    #first lets make a connection from db
    # we just pull a connection from db nothing else
    async with async_engine.connect() as connection:
        transaction=await connection.begin()

        # manually create the session
        async_session=AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False
        )
        # bind this session to a specific connection

        # pause and hand session to the caller
        yield async_session
        await async_session.close() # close session
        await transaction.rollback() # roll back the transaction

@pytest_asyncio.fixture(name="fastapi_client")
# another fixture -> this runs a fake browser on our code
async def client_fixture(session:AsyncSession, monkeypatch:MonkeyPatch):
    # we use client_fixture(session:AsyncSession) this runs the session fixture

    # override the database
    async def override_get_session():
        yield session
        # the fixture we defined
    app.dependency_overrides[get_session] = override_get_session

    # We create a fake async context manager just like the real WorkerSession
    @asynccontextmanager
    async def override_worker_session():
        # We create a new session just for the worker
        # But we bind it to session.bind (the exact same connection the test uses)
        worker_session = AsyncSession(
            bind=session.bind, 
            join_transaction_mode="create_savepoint",
            expire_on_commit=False
        )
        yield worker_session
        await worker_session.close()

    # We replace WorkerSession inside tasks.py and replace it with our safe version
    monkeypatch.setattr("app.tasks.WorkerSession", override_worker_session)


    #create the fake browser
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # normally httpx sends request over the internet
    # ASGITransport bypasses all of that
    # calls our FastAPI app directly in memory
    # no network, no port, no socket
    # FastAPI receives the request as if it came from network
    # but it never actually went on the network

    # base_url?
    #     httpx requires a valid base URL to construct requests
    # ac.get("/users") needs to know the full URL
    # becomes "http://test/users"

    # "test" is just a placeholder domain
    # never actually called
    # ASGITransport intercepts before any real network call
    # could be "http://anything" — doesn't matter

    app.dependency_overrides.clear()