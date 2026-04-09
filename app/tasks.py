# main issue
# our fastpai is running in async manner
# but celery works synchronously by default
# we have force/teach celery on how to work in async manner

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.db_models import Event

# Null Pool Concept
# We create a special engine just for the worker using NullPool.
# NullPool means "Open a connection, use it, and destroy it immediately."
# This prevents the "attached to a different loop" error.
worker_engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=True,
    poolclass=NullPool,
)

WorkerSession = async_sessionmaker(
    worker_engine, class_=AsyncSession, expire_on_commit=False
)


async def save_event_to_db(data: dict):
    async with WorkerSession() as session:
        event_db = Event(**data)
        session.add(event_db)
        await session.commit()
        await session.refresh(event_db)
        print(f"saved: {event_db.id}")
        return str(event_db.id)


# @celery_app.task turns this into a job that redis can triger
@celery_app.task
def process_event_task(event_data: dict):
    try:
        # Step 1: Try to find an already running event loop (Pytest Eager Mode)
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Step 2: Test Environment
        # A loop is already running! We schedule the DB write in the background 
        # instead of trying to force a new loop to start.
        loop.create_task(save_event_to_db(event_data))
        return "queued in existing loop"
    else:
        # Step 3: Production Environment
        # The Celery worker thread has no loop. We safely create one 
        # and run the database function synchronously.
        return asyncio.run(save_event_to_db(event_data))