"""add match item type

Revision ID: 9a31fa56887f
Revises: 6053b2dd2b53
Create Date: 2025-12-18 19:30:43.881659

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "9a31fa56887f"
down_revision: str | None = "6053b2dd2b53"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE item_type ADD VALUE 'MATCH';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def downgrade() -> None:
    # Enum values can't be removed easily in Postgres; no-op.
    return None
