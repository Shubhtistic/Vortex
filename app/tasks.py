from datetime import datetime, timezone
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

    # Major bug
    # during massives inserts sqlalchemy skipped the auto generated python timestamp variable
    # due to which many records had no date
    # so we manually add a timestap to these elements

    # Also postgres has a limit of max 64k parameters per query
    # so our db has 6 columns
    # so 6x10 -> 60k very close, if we even single new column this would go to 70k parameters
    # which would cause TooManyParameters Error

    # so lets use a simple 6k chunk size per batch

    total_inserted=0

    CHUNK_SIZE=6000



    async with WorkerSession() as session:


        for i in range(0,len(raw_events),CHUNK_SIZE):
            # lets say less than 6k events are present
            # in that case we cant jump by 6k elements
            # so this loop then starts at zero and runs once as it cant take 6k step interval

            chunk_strings=raw_events[i:i+CHUNK_SIZE]
            # in this case also if we go out of bounds
            # python wont throw errors it will just take whatever is present if does not have 6k events

            events_to_insert=[]

            batch_timestamp=datetime.now(timezone.utc)
            # timestamp for this entire batch

            for event_str in chunk_strings:

                event_dict=json.loads(event_str)

                event_dict["timestamp"]=batch_timestamp

                events_to_insert.append(event_dict)

            total_inserted=total_inserted+len(events_to_insert)

            # runs for every batch created
            await session.execute(insert(Event).values(events_to_insert))

        # final commit
        await session.commit()

    # delete the isolated bucket
    await redis.delete("process_buffer")
    
    print(f"Successfully batched {total_inserted} events to the database.")
    return True