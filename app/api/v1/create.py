from fastapi import APIRouter, Depends
from app.schemas.event import CreateEvent
from app.models.event_table import Event
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/track")
async def track_new_event(
    event_in: CreateEvent, session: AsyncSession = Depends(get_session)
):
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

    event_db = Event(**data)
    # ** means unpack a dictionary into keywrd arguments
    # **dict  →  spread the dict into arguments

    session.add(event_db)
    await session.commit()
    await session.refresh(event_db)

    return {"status": "saved", "event_id": event_db.id, "timestamp": event_db.timestamp}
