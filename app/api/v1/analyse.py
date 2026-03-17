from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import func, select, desc

from fastapi import APIRouter
from app.db.db_models import Event
from app.dependancies.db_dependancy import DbSessionDep
from app.dependancies.security import SecretKeyDep

router = APIRouter()


@router.get("/stats")
async def return_number(
    session: DbSessionDep,
    api_key: SecretKeyDep,
):
    statement = (
        select(func.count())
        .select_from(Event)
        .where(Event.tenant_id == api_key.tenant_id)
    )

    count = (await session.execute(statement)).scalar_one()

    return {"status": "Success", "tenant": api_key.tenant_id, "Total Count": count}


@router.get("/top-urls")
async def top_urls(
    db: DbSessionDep, api_key: SecretKeyDep, days_ago: int = 3, top: int = 5
):
    """Returns top 5 most visted urls for a tenant"""

    # days_ago -> a time duration for the data -> last 60 days (2 month approax), last 5 days, etc
    qry_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    query = (
        select(Event.url, func.count(Event.id).label("visits"))
        .where(Event.tenant_id == api_key.tenant_id)
        .where(Event.timestamp > qry_date)
        .group_by(Event.url)
        .order_by(desc("visits"))
        .limit(top)
    )
    res = await db.execute(query)

    all_rows = res.all()
    top_urls = []
    for row in all_rows:
        top_urls.append({"url": row.url, "visits": row.visits})

    return {"status": "success", "tenant": api_key.tenant_id, "data": top_urls}


@router.get("/events-per-day")
async def events_per_day(db: DbSessionDep, api_key: SecretKeyDep, from_days: int = 7):
    """Returns the number of events per day for a time-series chart."""

    qry_date = datetime.now(timezone.utc) - timedelta(days=from_days)

    date_column = func.date(Event.timestamp).label("event_date")

    query = (
        select(date_column, func.count(Event.id).label("visits"))
        .where(Event.tenant_id == api_key.tenant_id)
        .where(Event.timestamp > qry_date)  # Filter out old data FIRST
        .group_by(date_column)
        .order_by(date_column)
        # We removed .limit() because if we filter the last 7 days,
        # we naturally get a maximum of 7 groups back!
    )

    res = await db.execute(query)
    all_rows = res.all()

    daily_data = []
    for row in all_rows:
        daily_data.append({"date": str(row.event_date), "visits": row.visits})

    return {"status": "success", "tenant": api_key.tenant_id, "data": daily_data}
