from typing import Annotated
from fastapi import Depends
from redis.asyncio import Redis, ConnectionPool

from .config import get_settings

settings = get_settings()

# --- globals ---
_pool: ConnectionPool | None = None
_redis: Redis | None = None


async def init_redis() -> None:
    """call on app startup"""
    global _pool, _redis

    if _redis is not None:
        return

    _pool = ConnectionPool.from_url(
        settings.redis.redis_url,
        decode_responses=True,
        max_connections=50,
        socket_timeout=5,
        socket_connect_timeout=5,
        socket_keepalive=True,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    _redis = Redis(connection_pool=_pool)


def get_redis() -> Redis:
    """get redis client"""
    if _redis is None:
        raise RuntimeError(
            "Redis client not initialized — call init_redis() on startup first"
        )
    return _redis


async def get_redis_dep() -> Redis:
    """used in fastapi routes"""
    return get_redis()


# --- used in routers ---
RedisDep = Annotated[Redis, Depends(get_redis_dep)]


async def close_redis() -> None:
    """Call once on app shutdown"""
    global _pool, _redis

    if _redis is not None:
        await _redis.aclose()
        _redis = None

    if _pool is not None:
        await _pool.disconnect()
        _pool = None
