from typing import Annotated

import redis.asyncio as AsyncRedis
from fastapi import HTTPException, Depends, status, Security
from app.core.config import settings
from fastapi.security import APIKeyHeader

redis_client = AsyncRedis.from_url(settings.REDIS_URL, decode_responses=True)
# decode_responses=True means Redis will give us normal pythn strings instead of raw byte

api_key_header = APIKeyHeader(name="X-API-key", auto_error=False)


async def check_limit(api_key_header_value: str = Security(api_key_header)):
    # if no key
    if not api_key_header_value:
        return

    MAX_REQS = 1000
    WINDOW_SECONDS = 60

    # a bucket name for this requests
    redis_key = f"rate_limit:{api_key_header_value}"

    # add a counter
    current_count = await redis_client.incr(redis_key)

    # start 60 secs countdown on first request
    if current_count == 1:
        await redis_client.expire(redis_key, WINDOW_SECONDS)

    if current_count > MAX_REQS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {MAX_REQS} requests per {WINDOW_SECONDS} seconds.",
        )
