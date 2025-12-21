"""recommendation context and catalog fk

Revision ID: 26dccb19549f
Revises: b3cfe90abd0c
Create Date: 2025-12-21 00:24:12.775383

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "26dccb19549f"
down_revision: str | None = "b3cfe90abd0c"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("recommendation_instances", sa.Column("subject_id", sa.UUID(), nullable=True))
    op.add_column("recommendation_instances", sa.Column("term_id", sa.UUID(), nullable=True))
    op.add_column("recommendation_instances", sa.Column("topic_id", sa.UUID(), nullable=True))
    op.add_column(
        "recommendation_instances",
        sa.Column("recommendation_code", sa.String(), nullable=True),
    )

    op.create_foreign_key(
        "recommendation_instances_subject_id_fkey",
        "recommendation_instances",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "recommendation_instances_term_id_fkey",
        "recommendation_instances",
        "terms",
        ["term_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "recommendation_instances_topic_id_fkey",
        "recommendation_instances",
        "topics",
        ["topic_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "recommendation_instances_recommendation_code_fkey",
        "recommendation_instances",
        "recommendation_catalog",
        ["recommendation_code"],
        ["code"],
        ondelete="RESTRICT",
    )

    op.execute(
        """
        UPDATE recommendation_instances AS ri
        SET subject_id = s.subject_id
        FROM students AS s
        WHERE ri.student_id = s.id
          AND ri.subject_id IS NULL
          AND s.subject_id IS NOT NULL
        """
    )

    op.execute(
        """
        WITH latest_session AS (
            SELECT DISTINCT ON (student_id) student_id, term_id
            FROM activity_sessions
            WHERE term_id IS NOT NULL
            ORDER BY student_id, started_at DESC
        )
        UPDATE recommendation_instances AS ri
        SET term_id = ls.term_id
        FROM latest_session AS ls
        WHERE ri.student_id = ls.student_id
          AND ri.term_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE recommendation_instances AS ri
        SET recommendation_code = ri.rule_id
        WHERE ri.recommendation_code IS NULL
          AND ri.rule_id ~ '^R\\d\\d$'
          AND EXISTS (
              SELECT 1 FROM recommendation_catalog AS rc WHERE rc.code = ri.rule_id
          )
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        "recommendation_instances_recommendation_code_fkey",
        "recommendation_instances",
        type_="foreignkey",
    )
    op.drop_constraint(
        "recommendation_instances_topic_id_fkey",
        "recommendation_instances",
        type_="foreignkey",
    )
    op.drop_constraint(
        "recommendation_instances_term_id_fkey",
        "recommendation_instances",
        type_="foreignkey",
    )
    op.drop_constraint(
        "recommendation_instances_subject_id_fkey",
        "recommendation_instances",
        type_="foreignkey",
    )

    op.drop_column("recommendation_instances", "recommendation_code")
    op.drop_column("recommendation_instances", "topic_id")
    op.drop_column("recommendation_instances", "term_id")
    op.drop_column("recommendation_instances", "subject_id")
