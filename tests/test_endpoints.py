import json

import pytest
from sqlalchemy import select

from app.db.db_models import ApiKey,Event, KeyType
from app.utils.hash import hash_api_key

from app.tasks import save_batch
from app.core.redis import get_redis_pool

@pytest.mark.asyncio
async def test_track_event(fastapi_client,session):

    # step 1 -> Arrange

    tenant_id="vtx_tenant_shubham_000"
    raw_pub_key="vtx_pub_test_random_data" 

    db_pub_key=ApiKey(
        tenant_id=tenant_id,
        hashed_key=hash_api_key(raw_pub_key), key_type=KeyType.publishable,
    )

    # we use our mock db session
    session.add(db_pub_key)
    await session.commit()

    # we will send some fake data
    track_payload = {
        "url": "https://shubham.dev/blog",
        "event_type": "pageview",
        "payload": {"browser": "chrome"}
    }

    # step 2 -> ACT
    # our fake browser fires a request directly into our code
    # our endpoint also adds the data into redis
    response= await fastapi_client.post("/api/v1/track",
                                 json=track_payload,
                                 headers={"X-API-Key":raw_pub_key})


    # STEP 3 -> ASSERT
    assert response.status_code == 202
    data = response.json()

    assert data["status"]== "queued"
    assert data["message"] == "Event received and is being processed in background"


    # get a redis pool
    redis = await get_redis_pool()
    ctx = {"redis": redis}

    # manually run the worker to save data in batch
    worker_result = await save_batch(ctx)
    
    assert worker_result is True
    
    # Database check
    statement= select(Event).where(Event.tenant_id== tenant_id)
    result = await session.execute(statement)
    total_results= result.all()

    # we added only 1 event so there should exactly one event
    assert len(total_results) == 1