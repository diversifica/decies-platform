"""Baseline (schema managed by init SQL)

Revision ID: 0001_baseline
Revises:
Create Date: 2025-12-16

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
