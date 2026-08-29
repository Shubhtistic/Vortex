from typing import Optional
from datetime import datetime, timezone
from uuid import UUID, uuid7
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint

from .enums import MembershipRole


class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    name: str

    slug: str = Field(index=True, unique=True)

    is_active: bool = Field(default=True)

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


class OrganizationMembership(SQLModel, table=True):
    __tablename__ = "organization_memberships"

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    organization_id: UUID = Field(
        sa_column=Column(ForeignKey("organizations.id"), index=True, nullable=False)
    )

    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id"), index=True, nullable=False)
    )

    role: MembershipRole = Field(default=MembershipRole.analyst)

    is_active: bool = Field(default=True)

    invited_by_user_id: Optional[UUID] = Field(
        default=None, sa_column=Column(ForeignKey("users.id"))
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    __table_args__ = (
        # a user can only hold one ACTIVE membership row per org
        # (removed members can be re-invited — old inactive row no longer blocks it)
        Index(
            "uq_org_user_active",
            "organization_id",
            "user_id",
            unique=True,
            postgresql_where=Column("is_active") == True,
        ),
        # only one ACTIVE owner per org
        Index(
            "uq_one_owner_per_org",
            "organization_id",
            unique=True,
            postgresql_where=(Column("role") == MembershipRole.owner)
            & (Column("is_active") == True),
        ),
        # an email/user can be an ACTIVE owner in at most one org, globally
        Index(
            "uq_owner_globally_unique_per_user",
            "user_id",
            unique=True,
            postgresql_where=(Column("role") == MembershipRole.owner)
            & (Column("is_active") == True),
        ),
    )
