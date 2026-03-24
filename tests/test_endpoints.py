import pytest
from sqlalchemy import select
from app.db.db_models import ApiKey, KeyType, Event
from app.utils.hash import hash_api_key

# check auth without a api key being provided
@pytest.mark.asyncio
async def test_missing_api_key(client):
    # Act: Hit the endpoint with NO headers
    response = await client.get("/api/v1/stats")

    # Assert: Demand 401 Unauthorized
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing X-API-Key header"

#invalid api key
@pytest.mark.asyncio
async def test_invalid_api_key(client):
    # Arrange: Create a fake header
    fake_headers = {"X-API-Key": "vtx_sec_completely_fake_key"}

    # Act: Hit the endpoint with a fake key
    response = await client.get("/api/v1/stats", headers=fake_headers)

    # Assert: Demand 401 Unauthorized
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid or inactive api Key"


# Proves that a valid tenant with NO data shows 0 counts.

@pytest.mark.asyncio
async def test_stats_with_real_tenant(client, session):
    # step 1 -> Arrange
    tenant_id = "test_shubham_001"
    raw_key = "vtx_sec_test_123"

    new_key = ApiKey(
        tenant_id=tenant_id,
        hashed_key=hash_api_key(raw_key),
        key_type=KeyType.secret
    )
    
    session.add(new_key)
    await session.commit()
    await session.refresh(new_key)

    # step 2 -> Act
    headers = {"X-API-Key": raw_key}
    response = await client.get("/api/v1/stats", headers=headers)

    # step 3 -> Assert
    assert response.status_code == 200
    assert response.json()["tenant"] == tenant_id
    assert response.json()["Total Count"] == 0


# full working test
@pytest.mark.asyncio
async def test_track_event_and_check_stats(client, session):
    # step 1 -> Arrange
    tenant_id = "vortex_dev_shubham"
    
    # Insert two keys: One for public tracking, one for private stats
    raw_pub_key = "vtx_pub_test_123"
    pub_key = ApiKey(
        tenant_id=tenant_id,
        hashed_key=hash_api_key(raw_pub_key),
        key_type=KeyType.publishable
    )

    raw_sec_key = "vtx_sec_test_456"
    sec_key = ApiKey(
        tenant_id=tenant_id,
        hashed_key=hash_api_key(raw_sec_key),
        key_type=KeyType.secret
    )
    session.add_all([pub_key, sec_key])
    await session.commit()
    await session.refresh(pub_key)
    await session.refresh(sec_key)

    # step 2 -> Act: Track a pageview using the Publishable Key
    pub_headers = {"X-API-Key": raw_pub_key}
    payload = {
        "url": "https://shubham.dev/blog",
        "event_type": "pageview",
        "payload": {"browser": "chrome"}
    }
    
    track_response = await client.post("/api/v1/track", json=payload, headers=pub_headers)
    assert track_response.status_code == 202
    
    # step 3 -> Act: Check Stats using the Secret Key
    sec_headers = {"X-API-Key": raw_sec_key}
    stats_response = await client.get("/api/v1/stats", headers=sec_headers)

    # step 4 -> Assert
    assert stats_response.status_code == 200
    data = stats_response.json()
    assert data["tenant"] == tenant_id
    assert data["Total Count"] == 1

    # Final DB Verification: Check the actual row in vortex_test
    statement = select(Event).where(Event.tenant_id == tenant_id)
    result = await session.execute(statement)
    db_event = result.scalar_one()
    
    assert db_event.url == "https://shubham.dev/blog"
    assert db_event.event_type == "pageview"