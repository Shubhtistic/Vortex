from typing import Annotated
import logging
from fastapi import Depends
from redis.asyncio import Redis, BlockingConnectionPool
from redis.exceptions import ConnectionError as RedisConnectionError

from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# --- globals ---
class RedisPoolSaturatedError(RedisConnectionError):
    """Raised when Redis pool checkout times out, distinct from Redis being down."""


class BoundedRedisConnectionPool(BlockingConnectionPool):
    async def get_connection(self, *args, **kwargs):
        try:
            return await super().get_connection(*args, **kwargs)
        except RedisConnectionError as exc:
            if str(exc) == "No connection available.":
                raise RedisPoolSaturatedError(
                    "Timed out waiting for an available Redis connection"
                ) from exc
            raise


_pool: BoundedRedisConnectionPool | None = None
_redis: Redis | None = None


async def init_redis() -> None:
    """call on app startup"""
    global _pool, _redis

    if _redis is not None:
        logger.debug("Redis client already initialized")
        return

    _pool = BoundedRedisConnectionPool.from_url(
        settings.redis.redis_url,
        decode_responses=True,
        max_connections=settings.redis.max_connections,
        timeout=settings.redis.pool_timeout_seconds,
        socket_timeout=settings.redis.socket_timeout_seconds,
        socket_connect_timeout=5,
        socket_keepalive=True,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    _redis = Redis(connection_pool=_pool)
    logger.info("Redis client initialized")


def get_redis() -> Redis:
    """get redis client"""
    if _redis is None:
        logger.error("Redis client requested before initialization")
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

    logger.info("Redis client closed")
