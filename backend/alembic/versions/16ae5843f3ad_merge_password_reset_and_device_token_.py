"""merge password reset and device token branches

Revision ID: 16ae5843f3ad
Revises: 7a2e5c9d4b10, c9a3b8d6e5f4
Create Date: 2026-11-22 18:00:24.081746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16ae5843f3ad'
down_revision: Union[str, Sequence[str], None] = ('7a2e5c9d4b10', 'c9a3b8d6e5f4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
