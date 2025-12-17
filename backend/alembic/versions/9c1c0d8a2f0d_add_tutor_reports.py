"""Add tutor reports tables

Revision ID: 9c1c0d8a2f0d
Revises: fee3346a2bfe
Create Date: 2025-12-17 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "9c1c0d8a2f0d"
down_revision: str | None = "fee3346a2bfe"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tutor_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tutor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("term_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metrics_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("window_start", sa.DateTime(), nullable=True),
        sa.Column("window_end", sa.DateTime(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name="tutor_reports_student_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name="tutor_reports_subject_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["term_id"],
            ["terms.id"],
            name="tutor_reports_term_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tutor_id"],
            ["tutors.id"],
            name="tutor_reports_tutor_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="tutor_reports_pkey"),
    )
    op.create_index("idx_tutor_reports_student", "tutor_reports", ["student_id"], unique=False)
    op.create_index("idx_tutor_reports_tutor", "tutor_reports", ["tutor_id"], unique=False)
    op.create_index(
        "idx_tutor_reports_student_subject_term",
        "tutor_reports",
        ["student_id", "subject_id", "term_id"],
        unique=False,
    )

    op.create_table(
        "tutor_report_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("section_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["tutor_reports.id"],
            name="tutor_report_sections_report_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="tutor_report_sections_pkey"),
    )
    op.create_index(
        "idx_tutor_report_sections_report",
        "tutor_report_sections",
        ["report_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_tutor_report_sections_report", table_name="tutor_report_sections")
    op.drop_table("tutor_report_sections")
    op.drop_index("idx_tutor_reports_student_subject_term", table_name="tutor_reports")
    op.drop_index("idx_tutor_reports_tutor", table_name="tutor_reports")
    op.drop_index("idx_tutor_reports_student", table_name="tutor_reports")
    op.drop_table("tutor_reports")
