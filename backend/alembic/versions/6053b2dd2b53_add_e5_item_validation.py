"""add e5 item validation

Revision ID: 6053b2dd2b53
Revises: 749cf271a66c
Create Date: 2025-12-18 00:30:44.295888

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "6053b2dd2b53"
down_revision: str | None = "749cf271a66c"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE llm_run_step ADD VALUE 'E5_VALIDATE';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.add_column(
        "items",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column("items", sa.Column("source_chunk_index", sa.Integer(), nullable=True))
    op.add_column("items", sa.Column("validation_status", sa.String(length=20), nullable=True))
    op.add_column("items", sa.Column("validation_reason", sa.Text(), nullable=True))

    op.alter_column("items", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_column("items", "validation_reason")
    op.drop_column("items", "validation_status")
    op.drop_column("items", "source_chunk_index")
    op.drop_column("items", "is_active")
