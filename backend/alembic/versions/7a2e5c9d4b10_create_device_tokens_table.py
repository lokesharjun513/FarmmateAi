"""create device tokens table

Revision ID: 7a2e5c9d4b10
Revises: 9b7e4c1d2a6f
Create Date: 2026-10-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "7a2e5c9d4b10"

down_revision: str | Sequence[str] | None = "9b7e4c1d2a6f"

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


# ============================================================
# UPGRADE
# ============================================================


def upgrade() -> None:
    op.create_table(
        "device_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farmer_id", sa.UUID(), nullable=False),
        sa.Column("fid", sa.String(length=255), nullable=False),
        sa.Column("device_name", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_device_tokens_farmer_id",
        "device_tokens",
        ["farmer_id"],
    )

    op.create_index(
        "ix_device_token_fid",
        "device_tokens",
        ["fid"],
        unique=True,
    )


# ============================================================
# DOWNGRADE
# ============================================================


def downgrade() -> None:
    op.drop_index(
        "ix_device_token_fid",
        table_name="device_tokens",
    )

    op.drop_index(
        "ix_device_tokens_farmer_id",
        table_name="device_tokens",
    )

    op.drop_table("device_tokens")
