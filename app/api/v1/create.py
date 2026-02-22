from fastapi import APIRouter, Depends
from app.schemas.event import CreateEvent

from app.tasks import process_event_task
from app.dependancies.security import PublishableKeyDep
from app.dependancies.rate_limiter import check_limit

router = APIRouter()


@router.post(
    "/track", status_code=202, dependencies=[Depends(check_limit)]
)  # 202 means its accepted , we will work on it later
async def track_new_event(event_in: CreateEvent, api_key: PublishableKeyDep):
    """takes a new event and gives it to celery"""
    # Convert Schema -> Dictionary
    data = event_in.model_dump()

    # Postgres cannot store the Pydantic 'HttpUrl' object directly.
    data["url"] = str(data["url"])

    # add the tenant id
    data["tenant_id"] = api_key.tenant_id

    # .delay() means "Put this in Redis and don't wait for the answer"
    task = process_event_task.delay(data)

    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Event received and is being processed in background",
    }
