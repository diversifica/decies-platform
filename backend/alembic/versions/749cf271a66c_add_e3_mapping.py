"""add e3 mapping

Revision ID: 749cf271a66c
Revises: 6d2f0c3c1a7b
Create Date: 2025-12-18 00:17:02.790536

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "749cf271a66c"
down_revision: str | None = "6d2f0c3c1a7b"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE llm_run_step ADD VALUE 'E3_MAP';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.add_column(
        "knowledge_chunks",
        sa.Column("microconcept_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "knowledge_chunks_microconcept_id_fkey",
        "knowledge_chunks",
        "microconcepts",
        ["microconcept_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "knowledge_chunks_microconcept_id_fkey", "knowledge_chunks", type_="foreignkey"
    )
    op.drop_column("knowledge_chunks", "microconcept_id")
