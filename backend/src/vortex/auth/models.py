from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid7


class RefreshTokens(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: UUID = Field(primary_key=True, default_factory=uuid7)
    user_id: UUID = Field(foreign_key="users.id")
    org_id: UUID = Field(foreign_key="organizations.id")
    role: str

    is_revoked: bool = Field(default=False)

    hashed_token: str = Field(index=True, unique=True, max_length=64)

    # example -> expires_at + 90 days
    # users should not infinetely slide the window of expiry
    max_window_limit: datetime = Field(sa_column=Column(DateTime(timezone=True)))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))

    revoked_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
