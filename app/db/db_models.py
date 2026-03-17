from enum import Enum
from sqlmodel import SQLModel, Field, JSON
from typing import Optional, Dict, Any
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone
from uuid import UUID
from uuid_utils import uuid7


class KeyType(str, Enum):
    publishable = "publishable"
    secret = "secret"


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    # unique id
    id: UUID = Field(default_factory=uuid7, primary_key=True)

    # The string that logically links this key to the events
    tenant_id: str = Field(index=True)

    hashed_key: str = Field(index=True, unique=True)
    key_type: KeyType

    # turn off bad/malicious key
    is_active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    # This is how we know whose event this is. It logically matches ApiKey.tenant_id
    tenant_id: str = Field(index=True)

    # indexed so queries are fast later
    url: str = Field(index=True)

    event_type: str

    # sa_type=JSON is required to tell the database this is json object
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_type=JSON)

    # Timestamp: When did we save this?
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
