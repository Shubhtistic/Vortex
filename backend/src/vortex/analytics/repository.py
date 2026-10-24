from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.events.models import Event
from src.vortex.shared.database import execute_query


class AnalyticsRepository:
    @staticmethod
    def _scope_filters(
        organization_id: UUID,
        tenant_id: UUID | None,
        event_name: str | None,
    ) -> list:
        filters = [Event.organization_id == organization_id]
        if tenant_id is not None:
            filters.append(Event.tenant_id == tenant_id)
        if event_name is not None:
            filters.append(Event.event_name == event_name)
        return filters

    @staticmethod
    async def get_overview(
        organization_id: UUID,
        tenant_id: UUID | None,
        event_name: str | None,
        current_from: datetime,
        current_to: datetime,
        previous_from: datetime,
        db_session: AsyncSession,
    ):
        current_window = and_(
            Event.occurred_at >= current_from, Event.occurred_at < current_to
        )
        previous_window = and_(
            Event.occurred_at >= previous_from,
            Event.occurred_at < current_from,
        )
        stmt = (
            select(
                func.count(Event.id)
                .filter(current_window)
                .label("current_events"),
                func.count(Event.id)
                .filter(previous_window)
                .label("previous_events"),
                func.count(distinct(Event.person_id))
                .filter(current_window)
                .label("current_users"),
                func.count(distinct(Event.person_id))
                .filter(previous_window)
                .label("previous_users"),
                func.count(distinct(Event.session_id))
                .filter(current_window)
                .label("current_sessions"),
                func.count(distinct(Event.session_id))
                .filter(previous_window)
                .label("previous_sessions"),
            )
            .select_from(Event)
            .where(
                *AnalyticsRepository._scope_filters(
                    organization_id, tenant_id, event_name
                ),
                Event.occurred_at >= previous_from,
                Event.occurred_at < current_to,
            )
        )
        result = await execute_query(query=stmt, db_session=db_session)
        return result.one()

    @staticmethod
    async def get_timeseries(
        organization_id: UUID,
        tenant_id: UUID | None,
        event_name: str | None,
        start: datetime,
        end: datetime,
        interval: str,
        db_session: AsyncSession,
    ):
        bucket = func.date_trunc(interval, Event.occurred_at).label("bucket")
        stmt = (
            select(bucket, func.count(Event.id).label("count"))
            .where(
                *AnalyticsRepository._scope_filters(
                    organization_id, tenant_id, event_name
                ),
                Event.occurred_at >= start,
                Event.occurred_at < end,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        result = await execute_query(query=stmt, db_session=db_session)
        return result.all()

    @staticmethod
    async def get_top_events(
        organization_id: UUID,
        tenant_id: UUID | None,
        event_name: str | None,
        start: datetime,
        end: datetime,
        limit: int,
        db_session: AsyncSession,
    ):
        stmt = (
            select(Event.event_name, func.count(Event.id).label("count"))
            .where(
                *AnalyticsRepository._scope_filters(
                    organization_id, tenant_id, event_name
                ),
                Event.occurred_at >= start,
                Event.occurred_at < end,
            )
            .group_by(Event.event_name)
            .order_by(func.count(Event.id).desc(), Event.event_name)
            .limit(limit)
        )
        result = await execute_query(query=stmt, db_session=db_session)
        return result.all()

    @staticmethod
    async def get_breakdown(
        organization_id: UUID,
        tenant_id: UUID | None,
        event_name: str | None,
        start: datetime,
        end: datetime,
        property_name: str,
        limit: int,
        db_session: AsyncSession,
    ):
        property_value = Event.properties[property_name].as_string().label("value")
        stmt = (
            select(property_value, func.count(Event.id).label("count"))
            .where(
                *AnalyticsRepository._scope_filters(
                    organization_id, tenant_id, event_name
                ),
                Event.occurred_at >= start,
                Event.occurred_at < end,
                Event.properties[property_name].is_not(None),
            )
            .group_by(property_value)
            .order_by(func.count(Event.id).desc(), property_value)
            .limit(limit)
        )
        result = await execute_query(query=stmt, db_session=db_session)
        return result.all()

    @staticmethod
    async def get_active_users(
        organization_id: UUID,
        tenant_id: UUID | None,
        event_name: str | None,
        start: datetime,
        end: datetime,
        interval: str,
        db_session: AsyncSession,
    ):
        bucket = func.date_trunc(interval, Event.occurred_at).label("bucket")
        stmt = (
            select(bucket, func.count(distinct(Event.person_id)).label("active_users"))
            .where(
                *AnalyticsRepository._scope_filters(
                    organization_id, tenant_id, event_name
                ),
                Event.occurred_at >= start,
                Event.occurred_at < end,
                Event.person_id.is_not(None),
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        result = await execute_query(query=stmt, db_session=db_session)
        return result.all()

    @staticmethod
    async def get_recent_events(
        organization_id: UUID,
        tenant_id: UUID | None,
        event_name: str | None,
        start: datetime,
        end: datetime,
        limit: int,
        db_session: AsyncSession,
    ):
        stmt = (
            select(Event)
            .where(
                *AnalyticsRepository._scope_filters(
                    organization_id, tenant_id, event_name
                ),
                Event.occurred_at >= start,
                Event.occurred_at < end,
            )
            .order_by(Event.occurred_at.desc(), Event.id.desc())
            .limit(limit)
        )
        result = await execute_query(query=stmt, db_session=db_session)
        return result.scalars().all()
