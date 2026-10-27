"""create notifications table

Revision ID: 6cfd9aac8748
Revises: cf7b7e405fbe
Create Date: 2026-08-06 07:42:41.019145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6cfd9aac8748'
down_revision: Union[str, Sequence[str], None] = 'cf7b7e405fbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("farmer_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "AI_ADVISOR",
                "WEATHER",
                "SYSTEM",
                "GOVERNMENT",
                "DISEASE",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum(
                "HIGH",
                "MEDIUM",
                "LOW",
                name="notificationpriority",
            ),
            nullable=False,
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False),
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
        "ix_notifications_farmer_id",
        "notifications",
        ["farmer_id"],
    )

def downgrade() -> None:
    op.drop_index(
        "ix_notifications_farmer_id",
        table_name="notifications",
    )

    op.drop_table("notifications")