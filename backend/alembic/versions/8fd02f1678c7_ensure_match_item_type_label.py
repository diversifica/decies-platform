"""ensure MATCH item_type label

Revision ID: 8fd02f1678c7
Revises: 9a31fa56887f
Create Date: 2025-12-18 20:17:32.461507

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "8fd02f1678c7"
down_revision: str | None = "9a31fa56887f"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Some DBs may have applied an earlier migration that added 'match' instead of 'MATCH'.
    # SQLAlchemy stores enum member names (e.g. 'MATCH'), so we ensure that label exists.
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
