import asyncio, hmac, orjson
import logging
import random
from typing import Optional
from datetime import datetime, timezone
from fastapi import Header, HTTPException, status as http_status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from src.vortex.shared.database import get_session_factory

from src.vortex.shared.redis_client import get_redis

from .models import ApiKeyStatus
from .repository import ApiKeyRepository
from .utils import hash_api_key

logger = logging.getLogger(__name__)

# ========= TTL & LOCK VALUES ===========
LOCK_TIMEOUT = 5
LOCK_BLOCKING_TIMEOUT = 2
ACTIVE_KEY_TTL = 360
REVOKED_KEY_TTL = 300


# --- main function ----
async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    if x_api_key is None:
        logger.warning("API key authentication failed: key missing")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
        )

    hashed_key = hash_api_key(x_api_key)
    cache_key = f"vtx:{hashed_key}"
    try:
        redis = get_redis()
        return await _verify_using_cache_and_db(
            redis=redis,
            hashed_key=hashed_key,
            cache_key=cache_key,
        )
    except RedisError as e:
        logger.exception("Redis unavailable during API key verification")
        # try using only db if redis is down

        return await verify_with_db_only(hashed_key=hashed_key)


async def _verify_using_cache_and_db(
    redis: Redis,
    hashed_key: str,
    cache_key: str,
) -> dict:
    """Verfiy the key using both cache and db"""

    cached = await _get_cached(redis=redis, cache_key=cache_key)
    if cached:
        # either raise or return the data
        return _process_cache(cached=cached)

    # nothing was found in cache
    # use an lock so mulitple requests dont flood db
    async with redis.lock(
        f"lock:{cache_key}",
        timeout=LOCK_TIMEOUT,
        blocking_timeout=LOCK_BLOCKING_TIMEOUT,
    ):
        # double check
        cached = await _get_cached(redis=redis, cache_key=cache_key)
        if cached:
            return _process_cache(cached=cached)  # FIX: same - removed await

        # cache not found
        # now we will set it

        session_factory = get_session_factory()
        async with session_factory() as db_session:

            api_key_row = await _get_from_db(hashed_key, db_session)

            # check if api exists or is correct
            if api_key_row is None or not hmac.compare_digest(
                api_key_row.hashed_key, hashed_key
            ):
                logger.warning("API key authentication failed: key invalid")
                raise HTTPException(
                    status_code=http_status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )

            # process now
            if api_key_row.status == ApiKeyStatus.revoked:
                logger.warning("API key authentication failed: key revoked")

                # value
                value = {
                    "status": ApiKeyStatus.revoked.value,
                    "tenant_id": str(api_key_row.tenant_id),
                    "organization_id": str(api_key_row.organization_id),
                }

                # expiry with jitter
                ex = REVOKED_KEY_TTL + random.randint(-30, 30)

                # set the cache
                await redis.set(cache_key, orjson.dumps(value), ex=ex)

                # return response
                raise HTTPException(status_code=401, detail="API key revoked")

            # current_time
            now = datetime.now(timezone.utc)

            if api_key_row.grace_expires_at is not None:
                remaining = int((api_key_row.grace_expires_at - now).total_seconds())
                if remaining <= 0:
                    await ApiKeyRepository.set_as_revoked(
                        hashed_key=hashed_key, revoked_at=now, db_session=db_session
                    )
                    payload = {
                        "status": ApiKeyStatus.revoked.value,  # FIX: was enum object
                        "tenant_id": str(api_key_row.tenant_id),
                        "organization_id": str(api_key_row.organization_id),
                    }

                    # expiry with jitter
                    ex = REVOKED_KEY_TTL + random.randint(-30, 30)

                    await redis.set(cache_key, orjson.dumps(payload), ex=ex)
                    raise HTTPException(
                        status_code=http_status.HTTP_401_UNAUTHORIZED,
                        detail="API key revoked",
                    )

                # grace period still remains
                else:
                    logger.info("API key accepted during grace period")
                    payload = {
                        "status": ApiKeyStatus.grace_period.value,
                        "tenant_id": str(api_key_row.tenant_id),
                        "organization_id": str(api_key_row.organization_id),
                    }
                    await redis.set(cache_key, orjson.dumps(payload), ex=remaining)

                    return payload

            # key is activ
            payload = {
                "status": ApiKeyStatus.active.value,
                "tenant_id": str(api_key_row.tenant_id),
                "organization_id": str(api_key_row.organization_id),
            }

            # expiry with jitter

            ex = ACTIVE_KEY_TTL + random.randint(-30, 30)

            await redis.set(cache_key, orjson.dumps(payload), ex=ex)
            logger.debug("API key accepted from database and cached")
            return payload


async def verify_with_db_only(hashed_key: str):
    """this fetches the db directly for each request if redis is down"""

    session_factory = get_session_factory()
    async with session_factory() as db_session:

        try:
            api_key_row = await _get_from_db(
                hashed_key=hashed_key, db_session=db_session
            )

            # check if api key exists or is correct
            if api_key_row is None or not hmac.compare_digest(
                api_key_row.hashed_key, hashed_key
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )

            # process now
            if api_key_row.status == ApiKeyStatus.revoked:
                # return response
                raise HTTPException(status_code=401, detail="API key revoked")

            now = datetime.now(timezone.utc)

            if api_key_row.grace_expires_at is not None:
                remaining = int((api_key_row.grace_expires_at - now).total_seconds())
                if remaining <= 0:
                    await ApiKeyRepository.set_as_revoked(
                        hashed_key=hashed_key, revoked_at=now, db_session=db_session
                    )

                    raise HTTPException(
                        status_code=http_status.HTTP_401_UNAUTHORIZED,
                        detail="API key revoked",
                    )

                # grace period still remains
                else:
                    payload = {
                        "status": ApiKeyStatus.grace_period.value,
                        "tenant_id": str(api_key_row.tenant_id),
                        "organization_id": str(api_key_row.organization_id),
                    }

                    return payload

            payload = {
                "status": ApiKeyStatus.active.value,
                "tenant_id": str(api_key_row.tenant_id),
                "organization_id": str(api_key_row.organization_id),
            }
            return payload

        except OperationalError:
            raise HTTPException(
                status_code=503, detail="We Are Currently Facing Some issues"
            )


async def _get_from_db(hashed_key: str, db_session: AsyncSession) -> dict:
    try:
        return await ApiKeyRepository.get_auth_fields_by_hash(
            hashed_key=hashed_key, db_session=db_session
        )

    except OperationalError:
        raise HTTPException(
            status_code=503, detail="We Are Currently Facing Some issues"
        )


async def _get_cached(redis: Redis, cache_key: str) -> Optional[dict]:
    raw = await redis.get(cache_key)
    if raw:
        # load the data back
        return orjson.loads(raw)
    return None


def _process_cache(
    cached: dict,
):  # FIX: was async def - made sync, you were not awaiting it
    """if key is revoked raise else process and return data"""
    # FIX: compare.value because cached status is string from redis
    if cached["status"] == ApiKeyStatus.revoked.value:
        raise HTTPException(detail="Api key is revoked", status_code=401)

    return {
        "tenant_id": cached["tenant_id"],
        "organization_id": cached["organization_id"],
        "status": cached["status"],
    }
