from typing import Annotated

import redis.asyncio as AsyncRedis
from fastapi import HTTPException, Depends, status, Security
from app.core.config import settings
from fastapi.security import APIKeyHeader

redis_client = AsyncRedis.from_url(settings.REDIS_URL, decode_responses=True)
# decode_responses=True means Redis will give us normal pythn strings instead of raw byte

api_key_header = APIKeyHeader(name="X-API-key", auto_error=False)


# the outer function
def RateLimiter(max_reqs: int, window_seconds: int = 60):
    
    # inner dependancy
    async def _check_limit(api_key_header_value: str = Security(api_key_header)):
        if not api_key_header_value:
            return

        redis_key = f"rate_limit:{api_key_header_value}"
        
        # Increment the counter
        current_count = await redis_client.incr(redis_key)

        # Start the countdown timer on the first request
        if current_count == 1:
            await redis_client.expire(redis_key, window_seconds)

    
        if current_count > max_reqs:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_reqs} requests per {window_seconds} seconds.",
            )
            
    # return inner fucntion to fastapi
    return _check_limit