from typing import Any, Optional
from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.vortex.shared.utilities import reject_blank_text

from .enums import EventSource


# --- event input schema ---
class EventRequestSchema(BaseModel):
    """What the clients send us,
    Everything NOT in this schema (organization_id, tenant_id, api_key_id,
    person_id, group_id, ip_address, source, received_at, created_at) is
    resolved/derived server-side"""

    event: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Event name, e.g :- 'xyz_completed' or any $ event",
    )
    distinct_id: str = Field(..., min_length=1, max_length=200)

    # falls back to 'now' if not sent
    timestamp: Optional[datetime] = Field(
        default=None, description="Maps to occurred_at"
    )

    insert_id: Optional[str] = Field(
        default=None, max_length=200, description="Client given idempotency key"
    )
    session_id: Optional[UUID] = Field(default=None)

    properties: dict[str, Any] = Field(default_factory=dict)

    # --- $identify specific fields, optional on every other event ---
    anon_distinct_id: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Used only on $identify to merge an anonymous id into a known one",
    )
    person_properties: Optional[dict[str, Any]] = Field(default=None)

    # --- $group_identify specific fields, optional on every other event ---
    group_key: Optional[str] = Field(default=None, max_length=200)
    group_properties: Optional[dict[str, Any]] = Field(default=None)

    lib_version: Optional[str] = Field(default=None, max_length=50)

    _validate_text = field_validator(
        "event",
        "distinct_id",
        "insert_id",
        "anon_distinct_id",
        "group_key",
        "lib_version",
    )(reject_blank_text)

    @field_validator("event")
    @classmethod
    def event_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("event name cannot be blank")
        return stripped

    @field_validator("timestamp")
    @classmethod
    def default_to_now_if_missing(cls, v: Optional[datetime]) -> datetime:
        return v or datetime.now(timezone.utc)


# --- read schema ---
class EventReadSchema(BaseModel):

    id: UUID
    organization_id: UUID
    tenant_id: UUID
    api_key_id: UUID

    distinct_id: str
    person_id: Optional[UUID]
    session_id: Optional[UUID]
    group_id: Optional[UUID]

    event_name: str
    properties: dict[str, Any]
    person_properties: Optional[dict[str, Any]]
    group_properties: Optional[dict[str, Any]]

    insert_id: Optional[str]

    occurred_at: datetime
    received_at: datetime

    ip_address: Optional[str]
    user_agent: Optional[str]

    source: EventSource
    lib_version: Optional[str]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
