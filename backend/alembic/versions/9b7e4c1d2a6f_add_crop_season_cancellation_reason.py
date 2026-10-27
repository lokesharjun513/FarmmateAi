"""add crop season cancellation reason

Revision ID: 9b7e4c1d2a6f
Revises: 1ca38a27638e
Create Date: 2026-10-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "9b7e4c1d2a6f"

down_revision: str | Sequence[str] | None = "1ca38a27638e"

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


# ============================================================
# UPGRADE
# ============================================================


def upgrade() -> None:
    op.add_column(
        "crop_seasons",
        sa.Column(
            "cancellation_reason",
            sa.Text(),
            nullable=True,
        ),
    )


# ============================================================
# DOWNGRADE
# ============================================================


def downgrade() -> None:
    op.drop_column(
        "crop_seasons",
        "cancellation_reason",
    )
