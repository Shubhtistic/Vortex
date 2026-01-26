from sqlmodel import SQLModel, Field, JSON
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

# table = true -> make an tabke is absent


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Index: We make 'url' searchable so queries are fast later
    url: str = Field(index=True)

    event_type: str

    # sa_type=JSON is required to tell the database this is json object
    payload: Optional[Dict[str, Any]] = Field(default={}, sa_type=JSON)

    # 5. Timestamp: When did we save this?
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
