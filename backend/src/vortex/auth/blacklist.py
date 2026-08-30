from src.vortex.shared.redis_client import get_redis


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    redis = get_redis()
    await redis.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_blacklisted(jti: str) -> bool:
    redis = get_redis()
    return await redis.exists(f"blacklist:{jti}") == 1
