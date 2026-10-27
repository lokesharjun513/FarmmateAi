"""add crop season land fields

Revision ID: GENERATED_REVISION_ID
Revises: 6cfd9aac8748
Create Date: 2026-08-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e9253852cea9"
down_revision: Union[str, Sequence[str], None] = "6cfd9aac8748"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing crop season fields."""

    op.add_column(
        "crop_seasons",
        sa.Column(
            "land_area",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "crop_seasons",
        sa.Column(
            "land_unit",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.add_column(
        "crop_seasons",
        sa.Column(
            "harvested_date",
            sa.Date(),
            nullable=True,
        ),
    )

    # Backfill existing crop seasons from their farm.
    op.execute(
        """
        UPDATE crop_seasons AS cs
        SET
            land_area = f.land_area,
            land_unit = f.land_unit
        FROM farms AS f
        WHERE cs.farm_id = f.id
          AND cs.land_area IS NULL
        """
    )

    # The application model expects these fields to be required.
    op.alter_column(
        "crop_seasons",
        "land_area",
        existing_type=sa.Float(),
        nullable=False,
    )

    op.alter_column(
        "crop_seasons",
        "land_unit",
        existing_type=sa.String(length=20),
        nullable=False,
    )


def downgrade() -> None:
    """Remove crop season land fields."""

    op.drop_column("crop_seasons", "harvested_date")
    op.drop_column("crop_seasons", "land_unit")
    op.drop_column("crop_seasons", "land_area")