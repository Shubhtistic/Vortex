from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

import msgspec


EventName = Annotated[
    str, msgspec.Meta(min_length=1, max_length=200, pattern=r"\S")
]
DistinctId = Annotated[
    str, msgspec.Meta(min_length=1, max_length=200, pattern=r"\S")
]
OptionalText200 = Annotated[str, msgspec.Meta(max_length=200, pattern=r"\S")] | None
OptionalLibVersion = (
    Annotated[str, msgspec.Meta(max_length=50, pattern=r"\S")] | None
)


class EventIngestionSchema(msgspec.Struct):
    """Fast typed JSON decoder schema for the high-volume HTTP ingestion route."""

    event: EventName
    distinct_id: DistinctId
    timestamp: datetime | None = None
    insert_id: OptionalText200 = None
    session_id: UUID | None = None
    properties: dict[str, Any] = msgspec.field(default_factory=dict)
    anon_distinct_id: OptionalText200 = None
    person_properties: dict[str, Any] | None = None
    group_key: OptionalText200 = None
    group_properties: dict[str, Any] | None = None
    lib_version: OptionalLibVersion = None


EventIngestionBatch = Annotated[
    list[EventIngestionSchema], msgspec.Meta(min_length=1, max_length=1000)
]


class EventRecordSchema(EventIngestionSchema):
    """Validated client event plus server metadata for the Redpanda record."""

    raw_payload: EventIngestionSchema | None = None
    tenant_id: UUID | str | None = None
    organization_id: UUID | str | None = None
    api_key_id: UUID | str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    received_at: datetime | None = None
