"""recommendation versioning fields

Revision ID: d842d76c7e38
Revises: 26dccb19549f
Create Date: 2025-12-21 00:54:46.079980

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "d842d76c7e38"
down_revision: str | None = "26dccb19549f"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "recommendation_instances",
        sa.Column(
            "engine_version",
            sa.String(),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )
    op.add_column(
        "recommendation_instances",
        sa.Column(
            "ruleset_version",
            sa.String(),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )

    op.add_column(
        "recommendation_outcomes",
        sa.Column(
            "engine_version",
            sa.String(),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )
    op.add_column(
        "recommendation_outcomes",
        sa.Column(
            "ruleset_version",
            sa.String(),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )

    op.add_column(
        "tutor_reports",
        sa.Column(
            "engine_version",
            sa.String(),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )
    op.add_column(
        "tutor_reports",
        sa.Column(
            "ruleset_version",
            sa.String(),
            nullable=False,
            server_default=sa.text("'V1'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("tutor_reports", "ruleset_version")
    op.drop_column("tutor_reports", "engine_version")

    op.drop_column("recommendation_outcomes", "ruleset_version")
    op.drop_column("recommendation_outcomes", "engine_version")

    op.drop_column("recommendation_instances", "ruleset_version")
    op.drop_column("recommendation_instances", "engine_version")
