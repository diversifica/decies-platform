"""content_uploads processing status fields

Revision ID: 3f5f2c9e9b71
Revises: e88f5a4c0762
Create Date: 2025-12-21 13:22:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "3f5f2c9e9b71"
down_revision: str | None = "e88f5a4c0762"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "content_uploads", sa.Column("processing_status", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "content_uploads", sa.Column("processing_job_id", sa.String(length=128), nullable=True)
    )
    op.add_column("content_uploads", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column("content_uploads", sa.Column("processed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("content_uploads", "processed_at")
    op.drop_column("content_uploads", "processing_error")
    op.drop_column("content_uploads", "processing_job_id")
    op.drop_column("content_uploads", "processing_status")
