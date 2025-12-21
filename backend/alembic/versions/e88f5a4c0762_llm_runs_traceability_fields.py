"""llm_runs traceability fields

Revision ID: e88f5a4c0762
Revises: d842d76c7e38
Create Date: 2025-12-21 11:39:42.310312

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e88f5a4c0762"
down_revision: str | None = "d842d76c7e38"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "llm_runs",
        sa.Column("content_upload_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "llm_runs",
        sa.Column("knowledge_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "llm_runs",
        sa.Column("knowledge_chunk_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "llm_runs",
        sa.Column("attempt", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "llm_runs",
        sa.Column(
            "prompt_version",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )
    op.add_column(
        "llm_runs",
        sa.Column(
            "engine_version",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )
    op.add_column("llm_runs", sa.Column("error_message", sa.Text(), nullable=True))

    op.create_foreign_key(
        "llm_runs_content_upload_id_fkey",
        "llm_runs",
        "content_uploads",
        ["content_upload_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "llm_runs_knowledge_entry_id_fkey",
        "llm_runs",
        "knowledge_entries",
        ["knowledge_entry_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "llm_runs_knowledge_chunk_id_fkey",
        "llm_runs",
        "knowledge_chunks",
        ["knowledge_chunk_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("llm_runs", "attempt", server_default=None)
    op.alter_column("llm_runs", "prompt_version", server_default=None)
    op.alter_column("llm_runs", "engine_version", server_default=None)


def downgrade() -> None:
    op.drop_constraint("llm_runs_knowledge_chunk_id_fkey", "llm_runs", type_="foreignkey")
    op.drop_constraint("llm_runs_knowledge_entry_id_fkey", "llm_runs", type_="foreignkey")
    op.drop_constraint("llm_runs_content_upload_id_fkey", "llm_runs", type_="foreignkey")

    op.drop_column("llm_runs", "error_message")
    op.drop_column("llm_runs", "engine_version")
    op.drop_column("llm_runs", "prompt_version")
    op.drop_column("llm_runs", "attempt")
    op.drop_column("llm_runs", "knowledge_chunk_id")
    op.drop_column("llm_runs", "knowledge_entry_id")
    op.drop_column("llm_runs", "content_upload_id")
