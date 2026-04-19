import json
from app.db.db_models import Event
from sqlalchemy import NullPool, insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# nullpool -> open a connection and close it
# best for worker as it runs every 5 secs
worker_engine = create_async_engine(
    settings.POSTGRES_URL,
    poolclass=NullPool,
    echo=False,
)

WorkerSession = async_sessionmaker(
    worker_engine, class_=AsyncSession, expire_on_commit=False
)

async def save_batch(ctx):
    # extract the redis connection from the context
    redis=ctx["redis"]

    # the rename trick
    # rename the specific data that is in redis at that moment
    # doing this that key gets changed to new name and old one doest not exist
    # so then the endpoint creates a new one
    try:
        await redis.rename("vortex_buffer","process_buffer")
    except:
        # if vortex buffer is zero it means no active inserts
        return "no_events_to_add"
    
    # pull everything out of this bucket
    raw_events=await redis.lrange("process_buffer", 0, -1) # 0,-1 -> start and end index

    if not raw_events:
        await redis.delete("process_buffer")
        return "empty"
    # convert this json back into dict
    events_to_insert=[json.loads(event_str) for event_str in raw_events]

    async with WorkerSession() as session:
        await session.execute(insert(Event).values(events_to_insert))
        await session.commit()

    # delete the isolated bucket
    await redis.delete("process_buffer")
    
    print(f"Successfully batched {len(events_to_insert)} events to the database.")
    return True