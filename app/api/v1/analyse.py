from sqlmodel import func, select

from fastapi import APIRouter
from app.db.db_models import Event
from app.dependancies.db_dependancy import DbSessionDep

router = APIRouter()


@router.get("/stats")
async def return_number(session: DbSessionDep):
    s = select(func.count()).select_from(
        Event
    )  # sql query (Select count(*) from event; )

    count = (await session.execute(s)).scalar_one()
    return {" status": "Success", "Total Count": count}
