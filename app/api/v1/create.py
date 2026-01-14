from fastapi import APIRouter  ##   ,HTTPException
from app.schemas.event import CreateEvent

router = APIRouter()


@router.post("/track")
async def track_event(event: CreateEvent):
    print(f"✅ RECEIVED EVENT: {event.event_type} on {event.url}")

    return {
        "status": "received",
        "event_id": event.request_id,
        "processed_at": event.timestamp,
    }
