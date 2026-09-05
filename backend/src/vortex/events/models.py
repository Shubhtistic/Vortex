from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column, DateTime, ForeignKey, Index
from uuid_utils import uuid7


class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: UUID = Field(default_factory=uuid7, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(ForeignKey("tenants.id"), index=True, nullable=False)
    )
    api_key_id: UUID = Field(
        sa_column=Column(ForeignKey("api_keys.id"), index=True, nullable=False)
    )
    url: str = Field(index=True)
    event_type: str = Field(index=True)
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_type=JSON)
    session_id: Optional[str] = Field(default=None, index=True)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    __table_args__ = (Index("ix_events_tenant_timestamp", "tenant_id", "timestamp"),)
