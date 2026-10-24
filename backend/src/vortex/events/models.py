from typing import Optional, Any
from datetime import datetime, timezone
from uuid import UUID, uuid7
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, INET

from .enums import EventSource


# --- events Table ---
class Event(SQLModel, table=True):
    __tablename__ = "events"

    # no fk because we will later shift this table to clickhouse

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    organization_id: UUID = Field(index=True, nullable=False)
    tenant_id: UUID = Field(index=True, nullable=False)
    api_key_id: UUID = Field(index=True, nullable=False)

    distinct_id: str = Field(index=True)
    person_id: Optional[UUID] = Field(default=None, index=True)

    session_id: Optional[UUID] = Field(default=None, index=True)

    group_id: Optional[UUID] = Field(default=None, index=True)

    event_name: str = Field(index=True)

    properties: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    person_properties: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB)
    )
    group_properties: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB)
    )

    raw_payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    insert_id: Optional[str] = Field(default=None, max_length=200)

    occurred_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    ip_address: Optional[str] = Field(default=None, sa_column=Column(INET))
    user_agent: Optional[str] = Field(default=None, max_length=500)

    source: EventSource = Field(default=EventSource.api, index=True)
    lib_version: Optional[str] = Field(default=None, max_length=50)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "insert_id", name="uq_event_tenant_insert_id"),
        Index("ix_events_tenant_occurred_at", "tenant_id", "occurred_at"),
        Index("ix_events_tenant_distinct_id", "tenant_id", "distinct_id"),
    )


# Persons table
# one row for per end-user being tracked -> mutable
# stays in postgres so fk's kept
class Person(SQLModel, table=True):

    __tablename__ = "persons"

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    tenant_id: UUID = Field(
        sa_column=Column(ForeignKey("tenants.id"), index=True, nullable=False)
    )

    properties: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )


# one person can have multiple distinct id's
class PersonDistinctId(SQLModel, table=True):
    __tablename__ = "person_distinct_ids"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(ForeignKey("tenants.id"), index=True, nullable=False)
    )
    person_id: UUID = Field(
        sa_column=Column(ForeignKey("persons.id"), index=True, nullable=False)
    )
    distinct_id: str = Field(index=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "distinct_id", name="uq_tenant_distinct_id"),
    )


# one row per group level entities
class Group(SQLModel, table=True):
    __tablename__ = "groups"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(ForeignKey("tenants.id"), index=True, nullable=False)
    )

    group_key: str = Field(index=True)

    properties: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "group_key", name="uq_tenant_group_key"),
    )


# link table, person <-> group membership


class PersonGroup(SQLModel, table=True):
    __tablename__ = "person_groups"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    person_id: UUID = Field(
        sa_column=Column(ForeignKey("persons.id"), index=True, nullable=False)
    )
    group_id: UUID = Field(
        sa_column=Column(ForeignKey("groups.id"), index=True, nullable=False)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    __table_args__ = (
        UniqueConstraint("person_id", "group_id", name="uq_person_group"),
    )
