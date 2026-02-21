from enum import Enum
from sqlmodel import SQLModel, Field, JSON
from typing import Optional, Dict, Any
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone
import uuid

# table = true -> make an table is absent


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Index: We make 'url' searchable so queries are fast later
    url: str = Field(index=True)

    event_type: str

    # sa_type=JSON is required to tell the database this is json object
    payload: Optional[Dict[str, Any]] = Field(default={}, sa_type=JSON)

    # 5. Timestamp: When did we save this?
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    # # sa_column tells sqlodel to use a specific SQLAlchemy column type
    # DateTime(timezone=True) creates a 'TIMESTAMPTZ' column in Postgres


class KeyType(str, Enum):
    publishable = "publishable"
    secret = "secret"


class ApiKey(SQLModel, table=True):

    # unique id
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    tenant_id: str = Field(index=True)
    hashed_key: str = Field(index=True, unique=True)

    key_type: KeyType

    # turn off bad/malicious key
    is_active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
