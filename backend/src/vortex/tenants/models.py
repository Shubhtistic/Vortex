from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid7
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint

from .enums import TenantStatus


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"

    id: UUID = Field(primary_key=True, default_factory=uuid7)

    organization_id: UUID = Field(
        sa_column=Column(ForeignKey("organizations.id"), index=True, nullable=False)
    )

    tenant_name: str = Field(max_length=50)
    slug: str = Field(index=True, max_length=20)

    status: TenantStatus = Field(default=TenantStatus.active, index=True)

    created_by_user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id"), nullable=False)
    )

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

    archived_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_tenant_slug_per_org"),
    )
