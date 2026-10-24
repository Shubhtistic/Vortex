from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


AnalyticsInterval = Literal["hour", "day"]
ActiveUserInterval = Literal["day", "week", "month"]


class AnalyticsFilters(BaseModel):
    from_: datetime
    to: datetime
    event_name: str | None = None
    tenant_id: UUID | None = None


class MetricComparison(BaseModel):
    current: int
    previous: int
    change_percent: float | None


class OverviewResponse(BaseModel):
    total_events: MetricComparison
    unique_users: MetricComparison
    sessions: MetricComparison


class TimeSeriesPoint(BaseModel):
    bucket: datetime
    count: int


class RankedEvent(BaseModel):
    event_name: str
    count: int


class BreakdownValue(BaseModel):
    value: str
    count: int


class ActiveUsersPoint(BaseModel):
    bucket: datetime
    active_users: int


class RecentEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_name: str
    distinct_id: str
    person_id: UUID | None
    session_id: UUID | None
    properties: dict[str, Any]
    raw_payload: dict[str, Any]
    occurred_at: datetime
    received_at: datetime
