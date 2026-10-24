from datetime import datetime, timezone

from fastapi import APIRouter, Request

from src.vortex.tenants.dependencies import VerifyApiKeyDep
from src.vortex.shared.responses import ApiResponse

from .buffer import enqueue_events
from .schemas import EventBatchSchema, EventRequestSchema

# --- router ---
router = APIRouter(prefix="", tags=["events"])


def _event_payload(payload: EventRequestSchema, request: Request, api_key_info: dict):
    event = payload.model_dump()
    event["raw_payload"] = event.copy()
    event["tenant_id"] = api_key_info["tenant_id"]
    event["organization_id"] = api_key_info["organization_id"]
    event["api_key_id"] = api_key_info["api_key_id"]
    event["ip_address"] = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    event["user_agent"] = user_agent[:500] if user_agent else None
    event["received_at"] = datetime.now(timezone.utc)
    return event


@router.post("/events")
async def ingest_events(
    payload: EventBatchSchema,
    request: Request,
    api_key_info: VerifyApiKeyDep,
):
    events = [_event_payload(item, request, api_key_info) for item in payload]
    enqueue_events(events)

    return ApiResponse.success(
        message=f"Accepted {len(events)} events for processing", code=202
    )
