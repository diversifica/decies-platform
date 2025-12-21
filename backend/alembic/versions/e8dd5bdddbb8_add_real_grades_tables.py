"""add real grades tables

Revision ID: e8dd5bdddbb8
Revises: 6a2c2e6c0a12
Create Date: 2025-12-20 12:15:15.686585

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "e8dd5bdddbb8"
down_revision: str | None = "6a2c2e6c0a12"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "real_grades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("term_id", sa.UUID(), nullable=False),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("grade_value", sa.Numeric(6, 2), nullable=False),
        sa.Column("grading_scale", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_tutor_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name="real_grades_student_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name="real_grades_subject_id_fkey",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["term_id"],
            ["terms.id"],
            name="real_grades_term_id_fkey",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_tutor_id"],
            ["tutors.id"],
            name="real_grades_created_by_tutor_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_real_grades_student", "real_grades", ["student_id"])
    op.create_index("idx_real_grades_subject_term", "real_grades", ["subject_id", "term_id"])

    op.create_table(
        "assessment_scope_tags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("real_grade_id", sa.UUID(), nullable=False),
        sa.Column("topic_id", sa.UUID(), nullable=True),
        sa.Column("microconcept_id", sa.UUID(), nullable=True),
        sa.Column("weight", sa.Numeric(6, 4), nullable=True),
        sa.ForeignKeyConstraint(
            ["real_grade_id"],
            ["real_grades.id"],
            name="assessment_scope_tags_real_grade_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name="assessment_scope_tags_topic_id_fkey",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["microconcept_id"],
            ["microconcepts.id"],
            name="assessment_scope_tags_microconcept_id_fkey",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_assessment_scope_tags_grade",
        "assessment_scope_tags",
        ["real_grade_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_assessment_scope_tags_grade", table_name="assessment_scope_tags")
    op.drop_table("assessment_scope_tags")
    op.drop_index("idx_real_grades_subject_term", table_name="real_grades")
    op.drop_index("idx_real_grades_student", table_name="real_grades")
    op.drop_table("real_grades")
