from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import AnalyticsRepository
from .schemas import (
    ActiveUsersPoint,
    AnalyticsFilters,
    BreakdownValue,
    MetricComparison,
    OverviewResponse,
    RankedEvent,
    RecentEvent,
    TimeSeriesPoint,
)


class AnalyticsService:
    @staticmethod
    def _validated_range(filters: AnalyticsFilters) -> tuple[datetime, datetime]:
        start = filters.from_
        end = filters.to
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        else:
            start = start.astimezone(timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        else:
            end = end.astimezone(timezone.utc)
        if end <= start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="'to' must be later than 'from'",
            )
        if filters.event_name is not None and not filters.event_name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="event_name must not be blank",
            )
        return start, end

    @staticmethod
    def _comparison(current: int, previous: int) -> MetricComparison:
        change_percent = (
            round(((current - previous) / previous) * 100, 2)
            if previous
            else (0.0 if current == 0 else None)
        )
        return MetricComparison(
            current=current,
            previous=previous,
            change_percent=change_percent,
        )

    @staticmethod
    async def overview(
        organization_id: UUID,
        filters: AnalyticsFilters,
        db_session: AsyncSession,
    ) -> dict:
        start, end = AnalyticsService._validated_range(filters)
        row = await AnalyticsRepository.get_overview(
            organization_id=organization_id,
            tenant_id=filters.tenant_id,
            event_name=filters.event_name,
            current_from=start,
            current_to=end,
            previous_from=start - (end - start),
            db_session=db_session,
        )
        result = OverviewResponse(
            total_events=AnalyticsService._comparison(
                row.current_events, row.previous_events
            ),
            unique_users=AnalyticsService._comparison(
                row.current_users, row.previous_users
            ),
            sessions=AnalyticsService._comparison(
                row.current_sessions, row.previous_sessions
            ),
        )
        return result.model_dump()

    @staticmethod
    async def timeseries(
        organization_id: UUID,
        filters: AnalyticsFilters,
        interval: str,
        db_session: AsyncSession,
    ) -> list[dict]:
        start, end = AnalyticsService._validated_range(filters)
        rows = await AnalyticsRepository.get_timeseries(
            organization_id,
            filters.tenant_id,
            filters.event_name,
            start,
            end,
            interval,
            db_session,
        )
        return [
            TimeSeriesPoint(bucket=row.bucket, count=row.count).model_dump()
            for row in rows
        ]

    @staticmethod
    async def top_events(
        organization_id: UUID,
        filters: AnalyticsFilters,
        limit: int,
        db_session: AsyncSession,
    ) -> list[dict]:
        start, end = AnalyticsService._validated_range(filters)
        rows = await AnalyticsRepository.get_top_events(
            organization_id,
            filters.tenant_id,
            filters.event_name,
            start,
            end,
            limit,
            db_session,
        )
        return [
            RankedEvent(event_name=row.event_name, count=row.count).model_dump()
            for row in rows
        ]

    @staticmethod
    async def breakdown(
        organization_id: UUID,
        filters: AnalyticsFilters,
        property_name: str,
        limit: int,
        db_session: AsyncSession,
    ) -> list[dict]:
        start, end = AnalyticsService._validated_range(filters)
        property_name = property_name.strip()
        if not property_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="property must not be blank",
            )
        rows = await AnalyticsRepository.get_breakdown(
            organization_id,
            filters.tenant_id,
            filters.event_name,
            start,
            end,
            property_name,
            limit,
            db_session,
        )
        return [
            BreakdownValue(value=row.value, count=row.count).model_dump()
            for row in rows
        ]

    @staticmethod
    async def active_users(
        organization_id: UUID,
        filters: AnalyticsFilters,
        interval: str,
        db_session: AsyncSession,
    ) -> list[dict]:
        start, end = AnalyticsService._validated_range(filters)
        rows = await AnalyticsRepository.get_active_users(
            organization_id,
            filters.tenant_id,
            filters.event_name,
            start,
            end,
            interval,
            db_session,
        )
        return [
            ActiveUsersPoint(
                bucket=row.bucket, active_users=row.active_users
            ).model_dump()
            for row in rows
        ]

    @staticmethod
    async def recent_events(
        organization_id: UUID,
        filters: AnalyticsFilters,
        limit: int,
        db_session: AsyncSession,
    ) -> list[dict]:
        start, end = AnalyticsService._validated_range(filters)
        events = await AnalyticsRepository.get_recent_events(
            organization_id,
            filters.tenant_id,
            filters.event_name,
            start,
            end,
            limit,
            db_session,
        )
        return [RecentEvent.model_validate(event).model_dump() for event in events]
