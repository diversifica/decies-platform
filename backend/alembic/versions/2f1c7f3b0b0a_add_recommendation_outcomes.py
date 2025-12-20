"""add recommendation outcomes

Revision ID: 2f1c7f3b0b0a
Revises: e8dd5bdddbb8
Create Date: 2025-12-20 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "2f1c7f3b0b0a"
down_revision: str | None = "e8dd5bdddbb8"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "recommendation_instances",
        sa.Column("evaluation_window_days", sa.Integer(), server_default="14", nullable=False),
    )

    op.create_table(
        "recommendation_outcomes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("recommendation_id", sa.UUID(), nullable=False),
        sa.Column("evaluation_start", sa.DateTime(), nullable=False),
        sa.Column("evaluation_end", sa.DateTime(), nullable=False),
        sa.Column("success", sa.String(length=20), nullable=False),
        sa.Column("delta_mastery", sa.Numeric(10, 6), nullable=True),
        sa.Column("delta_retention", sa.Numeric(10, 6), nullable=True),
        sa.Column("delta_accuracy", sa.Numeric(10, 6), nullable=True),
        sa.Column("delta_hint_rate", sa.Numeric(10, 6), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["recommendation_instances.id"],
            name="recommendation_outcomes_recommendation_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recommendation_id",
            name="recommendation_outcomes_recommendation_id_key",
        ),
    )
    op.create_index(
        "idx_recommendation_outcomes_recommendation",
        "recommendation_outcomes",
        ["recommendation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_recommendation_outcomes_recommendation", table_name="recommendation_outcomes"
    )
    op.drop_table("recommendation_outcomes")
    op.drop_column("recommendation_instances", "evaluation_window_days")
