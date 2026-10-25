from datetime import datetime, timezone

import msgspec
from fastapi import APIRouter, HTTPException, Request, status

from src.vortex.tenants.dependencies import VerifyApiKeyDep
from src.vortex.shared.responses import ApiResponse

from .api_docs import EVENTS_OPENAPI_EXTRA
from .buffer import enqueue_events
from .schemas import EventIngestionBatch, EventIngestionSchema, EventRecordSchema

# --- router ---
router = APIRouter(prefix="", tags=["events"])
_event_decoder = msgspec.json.Decoder(EventIngestionBatch, strict=False)


def _event_payload(
    payload: EventIngestionSchema,
    request: Request,
    api_key_info: dict,
    ingested_at: datetime,
) -> EventRecordSchema:
    payload.event = payload.event.strip()
    if payload.timestamp is None:
        payload.timestamp = ingested_at

    user_agent = request.headers.get("user-agent")
    return EventRecordSchema(
        event=payload.event,
        distinct_id=payload.distinct_id,
        timestamp=payload.timestamp,
        insert_id=payload.insert_id,
        session_id=payload.session_id,
        properties=payload.properties,
        anon_distinct_id=payload.anon_distinct_id,
        person_properties=payload.person_properties,
        group_key=payload.group_key,
        group_properties=payload.group_properties,
        lib_version=payload.lib_version,
        raw_payload=payload,
        tenant_id=api_key_info["tenant_id"],
        organization_id=api_key_info["organization_id"],
        api_key_id=api_key_info["api_key_id"],
        ip_address=request.client.host if request.client else None,
        user_agent=user_agent[:500] if user_agent else None,
        received_at=ingested_at,
    )


@router.post(
    "/events",
    status_code=status.HTTP_202_ACCEPTED,
    openapi_extra=EVENTS_OPENAPI_EXTRA,
)
async def ingest_events(
    request: Request,
    api_key_info: VerifyApiKeyDep,
):
    try:
        payload: EventIngestionBatch = _event_decoder.decode(await request.body())
    except (msgspec.DecodeError, msgspec.ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "type": "event_payload_invalid",
                    "loc": ["body"],
                    "msg": str(exc),
                }
            ],
        ) from exc

    ingested_at = datetime.now(timezone.utc)
    events: list[EventRecordSchema] = [
        _event_payload(item, request, api_key_info, ingested_at) for item in payload
    ]
    enqueue_events(events)

    return ApiResponse.success(
        message=f"Accepted {len(events)} events for processing", code=202
    )
