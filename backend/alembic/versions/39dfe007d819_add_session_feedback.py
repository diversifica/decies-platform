"""add session feedback

Revision ID: 39dfe007d819
Revises: 8fd02f1678c7
Create Date: 2025-12-18 22:37:58.694364

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "39dfe007d819"
down_revision: str | None = "8fd02f1678c7"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("activity_sessions", sa.Column("feedback_rating", sa.Integer(), nullable=True))
    op.add_column("activity_sessions", sa.Column("feedback_text", sa.Text(), nullable=True))
    op.add_column(
        "activity_sessions", sa.Column("feedback_submitted_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("activity_sessions", "feedback_submitted_at")
    op.drop_column("activity_sessions", "feedback_text")
    op.drop_column("activity_sessions", "feedback_rating")
