from fastapi import status, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.future import select
from typing import Annotated

from app.dependancies.db_dependancy import DbSessionDep
from app.db.db_models import ApiKey, KeyType
from app.utils.hash import hash_api_key

from app.dependancies.rate_limiter import redis_client
import json

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key_header_value: Annotated[str, Security(api_key_header)],
    session: DbSessionDep,
) -> ApiKey:

    if api_key_header_value is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing X-API-Key header"
        )

    incoming_hash = hash_api_key(api_key_header_value)

    # cache logic
    cache_key = f"auth_cache:{incoming_hash}"

    # ask redis if it has this key
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        # redis has the key, now we dont have to query the db
        # we can just make a db object and return it
        data = json.loads(cached_data)
        return ApiKey(tenant_id=data["tenant_id"], key_type=data["key_type"])

    # if redis failed we have to do normal db lookup

    statement = select(ApiKey).where(ApiKey.hashed_key == incoming_hash)

    db_key = (await session.execute(statement)).scalar_one_or_none()

    if not db_key or not db_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or inactive api Key",
        )

    ## we save it for future in redis
    cache_payload = json.dumps(
        {
            "tenant_id": db_key.tenant_id,
            "key_type": db_key.key_type.value,
        }
    )

    # setex means Set with Expiration. We set it for 600 secs
    await redis_client.setex(cache_key, 600, cache_payload)
    return db_key


async def require_publishable_key(
    key: Annotated[ApiKey, Depends(verify_api_key)],
) -> ApiKey:
    if key.key_type != KeyType.publishable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="a publishable key is required for this endpoint",
        )
    return key


async def require_secret_key(key: Annotated[ApiKey, Depends(verify_api_key)]) -> ApiKey:
    if key.key_type != KeyType.secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="a secret key is needed for this endpoint",
        )
    return key


PublishableKeyDep = Annotated[ApiKey, Depends(require_publishable_key)]
SecretKeyDep = Annotated[ApiKey, Depends(require_secret_key)]
