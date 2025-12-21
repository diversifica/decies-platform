import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class TutorReport(Base):
    __tablename__ = "tutor_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id", name="tutor_reports_tutor_id_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", name="tutor_reports_student_id_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", name="tutor_reports_subject_id_fkey", ondelete="CASCADE"),
        nullable=False,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.id", name="tutor_reports_term_id_fkey", ondelete="CASCADE"),
        nullable=False,
    )

    engine_version: Mapped[str] = mapped_column(
        String,
        server_default=text("'V1'"),
        default="V1",
        nullable=False,
    )
    ruleset_version: Mapped[str] = mapped_column(
        String,
        server_default=text("'V1'"),
        default="V1",
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    sections: Mapped[list["TutorReportSection"]] = relationship(
        "TutorReportSection",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="TutorReportSection.order_index",
    )


class TutorReportSection(Base):
    __tablename__ = "tutor_report_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "tutor_reports.id",
            name="tutor_report_sections_report_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    report: Mapped["TutorReport"] = relationship("TutorReport", back_populates="sections")
