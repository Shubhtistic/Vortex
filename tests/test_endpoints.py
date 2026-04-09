import pytest
from sqlalchemy import select
import asyncio

from app.db.db_models import ApiKey,Event, KeyType
from app.utils.hash import hash_api_key

@pytest.mark.asyncio
async def test_track_event(fastapi_client,session):

    # step 1 -> Arrange

    tenant_id="vtx_tenant_shubham_000"
    raw_pub_key="vtx_pub_test_random_data" 

    db_pub_key=ApiKey(
        tenant_id=tenant_id,
        hashed_key=hash_api_key(raw_pub_key), key_type=KeyType.publishable,
    )

    # we use our mok db session
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
    response= await fastapi_client.post("/api/v1/track",
                                 json=track_payload,
                                 headers={"X-API-Key":raw_pub_key})

    # now we wait for 1 sec to let celery finish its background tasks
    await asyncio.sleep(1)    
    
    # STEP 3 -> ASSERT
    assert response.status_code == 202
    data = response.json()

    assert data["status"]== "queued"
    assert data["message"] == "Event received and is being processed in background"
    assert data["task_id"] is not None

    # Database check
    statement= select(Event).where(Event.tenant_id== tenant_id)
    result = await session.execute(statement)
    total_results= result.all()

    # we added only 1 event so there should exactly one event
    assert len(total_results) == 1