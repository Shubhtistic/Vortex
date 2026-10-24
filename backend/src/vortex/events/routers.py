from datetime import datetime, timezone

from fastapi import APIRouter, Request

from src.vortex.tenants.dependencies import VerifyApiKeyDep
from src.vortex.shared.responses import ApiResponse
from src.vortex.shared.config import get_settings
from src.vortex.shared.redpanda_client import RedpandaProducer

from .schemas import EventRequestSchema

# --- router ---
router = APIRouter(prefix="", tags=["events"])


@router.post("/events")
async def ingest_event(
    payload: EventRequestSchema,
    request: Request,
    api_key_info: VerifyApiKeyDep,
):
    event = payload.model_dump()
    event["raw_payload"] = event.copy()
    event["tenant_id"] = api_key_info["tenant_id"]
    event["organization_id"] = api_key_info["organization_id"]
    event["api_key_id"] = api_key_info["api_key_id"]
    event["ip_address"] = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    event["user_agent"] = user_agent[:500] if user_agent else None
    event["received_at"] = datetime.now(timezone.utc)

    await RedpandaProducer.send_event(
        event,
        topic=get_settings().redpanda.events_topic,
    )

    return ApiResponse.success(message="Successfully sent the event", code=202)
