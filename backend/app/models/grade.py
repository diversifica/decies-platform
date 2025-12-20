import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class RealGrade(Base):
    __tablename__ = "real_grades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", name="real_grades_student_id_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", name="real_grades_subject_id_fkey", ondelete="RESTRICT"),
        nullable=False,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.id", name="real_grades_term_id_fkey", ondelete="RESTRICT"),
        nullable=False,
    )
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    grade_value: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    grading_scale: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id", name="real_grades_created_by_tutor_id_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )

    scope_tags: Mapped[list["AssessmentScopeTag"]] = relationship(
        "AssessmentScopeTag",
        back_populates="real_grade",
        cascade="all, delete-orphan",
        order_by="AssessmentScopeTag.id",
    )


class AssessmentScopeTag(Base):
    __tablename__ = "assessment_scope_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    real_grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "real_grades.id", name="assessment_scope_tags_real_grade_id_fkey", ondelete="CASCADE"
        ),
        nullable=False,
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", name="assessment_scope_tags_topic_id_fkey", ondelete="SET NULL"),
        nullable=True,
    )
    microconcept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "microconcepts.id",
            name="assessment_scope_tags_microconcept_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    weight: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)

    real_grade: Mapped["RealGrade"] = relationship("RealGrade", back_populates="scope_tags")
