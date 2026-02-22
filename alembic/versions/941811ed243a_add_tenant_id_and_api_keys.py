"""Add tenant_id and api_keys

Revision ID: 941811ed243a
Revises: 911d0c27ec53
Create Date: 2026-02-22 16:03:22.910738
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers
revision: str = "941811ed243a"
down_revision: Union[str, Sequence[str], None] = "911d0c27ec53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # new api keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("hashed_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "key_type",
            sa.Enum("publishable", "secret", name="keytype"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_api_keys_hashed_key"),
        "api_keys",
        ["hashed_key"],
        unique=True,
    )

    op.create_index(
        op.f("ix_api_keys_tenant_id"),
        "api_keys",
        ["tenant_id"],
        unique=False,
    )

    # add tenant_id column as NULL first
    op.add_column(
        "events",
        sa.Column(
            "tenant_id",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )

    # Backfill existing rows
    op.execute("UPDATE events SET tenant_id = 'legacy_tenant' WHERE tenant_id IS NULL")

    # Enforce NOT NULL after data is valid
    op.alter_column(
        "events",
        "tenant_id",
        nullable=False,
    )

    # Create index
    op.create_index(
        op.f("ix_events_tenant_id"),
        "events",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f("ix_events_tenant_id"), table_name="events")
    op.drop_column("events", "tenant_id")

    op.drop_index(op.f("ix_api_keys_tenant_id"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_hashed_key"), table_name="api_keys")
    op.drop_table("api_keys")
