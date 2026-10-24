import asyncio, hmac, orjson
import logging
import random
from contextlib import asynccontextmanager
from typing import Annotated, Optional
from datetime import datetime, timezone
from cachetools import TTLCache
from fastapi import Depends, Header, HTTPException, status as http_status
from redis.asyncio import Redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    LockError,
    RedisError,
    TimeoutError as RedisTimeoutError,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from src.vortex.shared.database import get_session_factory

from src.vortex.shared.config import get_settings
from src.vortex.shared.redis_client import RedisPoolSaturatedError, get_redis

from .models import ApiKeyStatus
from .repository import ApiKeyRepository
from .utils import hash_api_key

logger = logging.getLogger(__name__)
settings = get_settings()

# ========= TTL & LOCK VALUES ===========
LOCK_TIMEOUT = 5
LOCK_BLOCKING_TIMEOUT = 2
LOCK_CACHE_RECHECK_ATTEMPTS = 10
LOCK_CACHE_RECHECK_INTERVAL = 0.05
ACTIVE_KEY_TTL = 360
REVOKED_KEY_TTL = 300

_api_key_cache: TTLCache[str, dict] = TTLCache(
    maxsize=settings.redis.api_key_cache_max_size,
    ttl=settings.redis.api_key_cache_ttl_seconds,
)
_api_key_locks: dict[str, tuple[asyncio.Lock, int]] = {}
_api_key_locks_guard = asyncio.Lock()
_db_fallback_semaphore = asyncio.Semaphore(settings.redis.db_fallback_concurrency)


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
    cached = _get_local_cached_key(hashed_key)
    if cached is not None:
        return _process_cache(cached)

    # A process-local single-flight lock keeps concurrent requests for a hot
    # key from all querying Redis while its local cache entry is missing.
    async with _singleflight_api_key(cache_key):
        cached = _get_local_cached_key(hashed_key)
        if cached is not None:
            return _process_cache(cached)

        redis = get_redis()
        try:
            result = await _verify_using_cache_and_db(
                redis=redis,
                hashed_key=hashed_key,
                cache_key=cache_key,
            )
        except LockError:
            # A lock timeout means another process may still be filling Redis.
            # Recheck briefly before using the bounded database fallback.
            logger.debug("Timed out waiting for API key cache lock; rechecking cache")
            try:
                cached = await _wait_for_cached_key(redis=redis, cache_key=cache_key)
            except RedisPoolSaturatedError:
                raise _redis_saturated_response()
            except RedisTimeoutError:
                raise _redis_saturated_response()
            except RedisConnectionError:
                logger.exception("Redis unavailable while rechecking API key cache")
                result = await _bounded_db_fallback(hashed_key)
            except RedisError:
                logger.exception("Redis error while rechecking API key cache")
                raise _redis_error_response()
            else:
                if cached:
                    result = _process_cache(cached)
                else:
                    logger.warning(
                        "API key cache remained empty after lock timeout; "
                        "verifying against DB"
                    )
                    result = await _bounded_db_fallback(hashed_key)
        except RedisPoolSaturatedError:
            raise _redis_saturated_response()
        except RedisTimeoutError:
            raise _redis_saturated_response()
        except RedisConnectionError:
            logger.exception("Redis unavailable during API key verification")
            result = await _bounded_db_fallback(hashed_key)
        except RedisError:
            logger.exception("Redis error during API key verification")
            raise _redis_error_response()

        _cache_api_key_result(hashed_key, result)
        return result


def _redis_saturated_response() -> HTTPException:
    logger.warning("Redis connection pool saturated during API key verification")
    return HTTPException(
        status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication is temporarily busy; retry shortly",
        headers={"Retry-After": "1"},
    )


def _redis_error_response() -> HTTPException:
    return HTTPException(
        status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication service is temporarily unavailable",
        headers={"Retry-After": "1"},
    )


def _get_local_cached_key(hashed_key: str) -> Optional[dict]:
    return _api_key_cache.get(hashed_key)


def _cache_api_key_result(hashed_key: str, result: dict) -> None:
    # Grace-period keys may expire before the general local-cache TTL ends.
    if result.get("status") == ApiKeyStatus.grace_period.value:
        return
    _api_key_cache[hashed_key] = result


@asynccontextmanager
async def _singleflight_api_key(cache_key: str):
    async with _api_key_locks_guard:
        entry = _api_key_locks.get(cache_key)
        if entry is None:
            lock = asyncio.Lock()
            _api_key_locks[cache_key] = (lock, 1)
        else:
            lock, users = entry
            _api_key_locks[cache_key] = (lock, users + 1)

    try:
        async with lock:
            yield
    finally:
        async with _api_key_locks_guard:
            lock, users = _api_key_locks[cache_key]
            if users == 1:
                _api_key_locks.pop(cache_key, None)
            else:
                _api_key_locks[cache_key] = (lock, users - 1)


async def _bounded_db_fallback(hashed_key: str) -> dict:
    try:
        await asyncio.wait_for(
            _db_fallback_semaphore.acquire(),
            timeout=settings.redis.db_fallback_wait_seconds,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily busy; retry shortly",
            headers={"Retry-After": "1"},
        ) from exc

    try:
        return await verify_with_db_only(hashed_key=hashed_key)
    finally:
        _db_fallback_semaphore.release()


async def _wait_for_cached_key(redis: Redis, cache_key: str) -> Optional[dict]:
    """Recheck briefly while the request holding the cache lock fills the key."""
    for attempt in range(LOCK_CACHE_RECHECK_ATTEMPTS):
        cached = await _get_cached(redis=redis, cache_key=cache_key)
        if cached:
            return cached

        if attempt + 1 < LOCK_CACHE_RECHECK_ATTEMPTS:
            await asyncio.sleep(LOCK_CACHE_RECHECK_INTERVAL)

    return None


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
                    "api_key_id": str(api_key_row.id),
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
                        "api_key_id": str(api_key_row.id),
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
                        "api_key_id": str(api_key_row.id),
                        "tenant_id": str(api_key_row.tenant_id),
                        "organization_id": str(api_key_row.organization_id),
                    }
                    await redis.set(cache_key, orjson.dumps(payload), ex=remaining)

                    return payload

            # key is activ
            payload = {
                "status": ApiKeyStatus.active.value,
                "api_key_id": str(api_key_row.id),
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
                        "api_key_id": str(api_key_row.id),
                        "tenant_id": str(api_key_row.tenant_id),
                        "organization_id": str(api_key_row.organization_id),
                    }

                    return payload

            payload = {
                "status": ApiKeyStatus.active.value,
                "api_key_id": str(api_key_row.id),
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
        "api_key_id": cached["api_key_id"],
        "tenant_id": cached["tenant_id"],
        "organization_id": cached["organization_id"],
        "status": cached["status"],
    }


# === Api Key Auth Dependency ====

VerifyApiKeyDep = Annotated[dict, Depends(verify_api_key)]
