"""add CLOZE item type

Revision ID: 6a2c2e6c0a12
Revises: 39dfe007d819
Create Date: 2025-12-20 00:00:00.000000

"""

from __future__ import annotations

from alembic import op

revision: str = "6a2c2e6c0a12"
down_revision: str | None = "39dfe007d819"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # SQLAlchemy stores enum member names (e.g. 'CLOZE'), so we ensure that label exists.
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE item_type ADD VALUE 'CLOZE';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def downgrade() -> None:
    # Enum values can't be removed easily in Postgres; no-op.
    return None
