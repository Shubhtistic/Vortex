from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid7
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint

from .enums import ApiKeyStatus, TenantStatus


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


class ApiKey(SQLModel, table=True):

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    organization_id: UUID = Field(
        sa_column=Column(ForeignKey("organizations.id"), index=True, nullable=False)
    )

    tenant_id: UUID = Field(
        sa_column=Column(ForeignKey("tenants.id"), index=True, nullable=False)
    )

    # api key slug
    api_key_slug: str = Field(max_length=20, unique=True)

    # show very small preview of raw api key value on frontend, last 4-5 letters
    api_key_raw_preview: str = Field(max_length=5)

    # actual hashed value
    hashed_key: str

    status: ApiKeyStatus = Field(default=ApiKeyStatus.active)

    grace_expires_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    created_by_user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id"), nullable=False)
    )
    # also we add grace time to this, exact time api key stopped taking reqs
    revoked_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    # example -> api key slug name changed
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
    )
