from uuid import uuid4

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
    # api_key_info:VerifyApiKeyDep,
):
    # event = payload.model_dump()
    # event["tenant_id"] = str(api_key_info.tenant_id)
    # event["organization_id"] = str(api_key_info.organization_id)
    # event["api_key_id"] = str(api_key_info.id)
    # event["ip_address"] = request.client.host
    # event["user_agent"] = request.headers.get("user-agent")

    event = payload.model_dump()
    event["tenant_id"] = str(uuid4())
    event["organization_id"] = str(uuid4())
    event["api_key_id"] = str(uuid4())
    event["ip_address"] = request.client.host
    event["user_agent"] = request.headers.get("user-agent")

    await RedpandaProducer.send_event(
        event,
        topic=get_settings().redpanda.events_topic,
    )

    return ApiResponse.success(message="Successfully sent the event", code=202)
