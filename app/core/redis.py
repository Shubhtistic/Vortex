# using this we tell our fastapi app how to talk to arq
# we create redis pool for it
from arq import create_pool
from app.core.config import settings
from arq.connections import RedisSettings

# this tell redis to how to connect to our redis
REDIS_SETTINGS=RedisSettings(host=settings.REDIS_HOST, port=6379)

# We will store the pool in a global variable so the whole app can share it
redis_pool = None

async def init_redis_pool():
    global redis_pool # use the global var and dont make a new one
    redis_pool= await create_pool(REDIS_SETTINGS)
async def close_redis_pool():
    global redis_pool
    if redis_pool:
        await redis_pool.close()

async def get_redis_pool():
    if not redis_pool:
        raise RuntimeError("Redis pool is not initialized")
    return redis_pool