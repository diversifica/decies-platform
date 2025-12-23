"""merge games table branch

Revision ID: 18617bb11e18
Revises: 3f5f2c9e9b71, f7c3d55b6bf7
Create Date: 2025-12-23 16:21:43.644880

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = '18617bb11e18'
down_revision: str | None = ('3f5f2c9e9b71', 'f7c3d55b6bf7')
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
