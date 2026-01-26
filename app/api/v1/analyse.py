from app.db.session import get_session
from sqlmodel import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from fastapi import APIRouter
from app.models.event_table import Event

router = APIRouter()


@router.get("/stats")
async def return_number(session: AsyncSession = Depends(get_session)):
    s = select(func.count()).select_from(
        Event
    )  # sql query (Select count(*) from event; )

    count = await session.exec(s).one()
    return {" status": "Success", "Total Count": count}
