from fastapi import APIRouter
from app.schemas.event import CreateEvent

from app.tasks import process_event_task

router = APIRouter()


@router.post(
    "/track", status_code=202
)  # 202 means its accepted , we will work on it later
async def track_new_event(event_in: CreateEvent):
    """
    Docstring for track_new_event

    :param event_in: new event to be added in database
    :type event_in: CreateEvent
    :param session: db session to perform operations
    :type session: AsyncSession
    """
    # Convert Schema -> Dictionary
    data = event_in.model_dump()

    # Postgres cannot store the Pydantic 'HttpUrl' object directly.
    data["url"] = str(data["url"])

    # .delay() means "Put this in Redis and don't wait for the answer"
    task = process_event_task.delay(data)

    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Event received and is being processed in background",
    }
