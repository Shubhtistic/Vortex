from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.vortex.auth.dependencies import CurrentUserDep
from src.vortex.shared.database import DbSessionDep
from src.vortex.shared.responses import ApiResponse

from .schemas import AnalyticsFilters
from .service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_filters(
    from_: datetime = Query(alias="from"),
    to: datetime = Query(),
    event_name: str | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None),
) -> AnalyticsFilters:
    return AnalyticsFilters(
        from_=from_, to=to, event_name=event_name, tenant_id=tenant_id
    )


AnalyticsFiltersDep = Annotated[AnalyticsFilters, Depends(get_analytics_filters)]


@router.get("/overview")
async def get_overview(
    filters: AnalyticsFiltersDep,
    db_session: DbSessionDep,
    current_user: CurrentUserDep,
):
    result = await AnalyticsService.overview(
        organization_id=current_user["org_id"],
        filters=filters,
        db_session=db_session,
    )
    return ApiResponse.success(
        message="Analytics overview fetched", data=result
    )


@router.get("/timeseries")
async def get_timeseries(
    filters: AnalyticsFiltersDep,
    db_session: DbSessionDep,
    current_user: CurrentUserDep,
    interval: Literal["hour", "day"] = Query(default="day"),
):
    result = await AnalyticsService.timeseries(
        organization_id=current_user["org_id"],
        filters=filters,
        interval=interval,
        db_session=db_session,
    )
    return ApiResponse.success(
        message="Analytics timeseries fetched", data=result
    )


@router.get("/top-events")
async def get_top_events(
    filters: AnalyticsFiltersDep,
    db_session: DbSessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(default=10, ge=1, le=100),
):
    result = await AnalyticsService.top_events(
        organization_id=current_user["org_id"],
        filters=filters,
        limit=limit,
        db_session=db_session,
    )
    return ApiResponse.success(
        message="Top events fetched", data=result
    )


@router.get("/breakdown")
async def get_breakdown(
    filters: AnalyticsFiltersDep,
    db_session: DbSessionDep,
    current_user: CurrentUserDep,
    property_name: str = Query(..., alias="property", min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=100),
):
    result = await AnalyticsService.breakdown(
        organization_id=current_user["org_id"],
        filters=filters,
        property_name=property_name,
        limit=limit,
        db_session=db_session,
    )
    return ApiResponse.success(
        message="Analytics breakdown fetched", data=result
    )


@router.get("/active-users")
async def get_active_users(
    filters: AnalyticsFiltersDep,
    db_session: DbSessionDep,
    current_user: CurrentUserDep,
    interval: Literal["day", "week", "month"] = Query(default="day"),
):
    result = await AnalyticsService.active_users(
        organization_id=current_user["org_id"],
        filters=filters,
        interval=interval,
        db_session=db_session,
    )
    return ApiResponse.success(
        message="Active users fetched", data=result
    )


@router.get("/events/recent")
async def get_recent_events(
    filters: AnalyticsFiltersDep,
    db_session: DbSessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(default=50, ge=1, le=200),
):
    result = await AnalyticsService.recent_events(
        organization_id=current_user["org_id"],
        filters=filters,
        limit=limit,
        db_session=db_session,
    )
    return ApiResponse.success(
        message="Recent events fetched", data=result
    )
