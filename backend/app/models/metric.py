import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MetricAggregate(Base):
    __tablename__ = "metric_aggregates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", name="metric_aggregates_student_id_fkey"),
        nullable=False,
    )
    scope_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # subject, term, topic, microconcept, activity_type
    scope_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    first_attempt_accuracy: Mapped[float | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    error_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    median_response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempts_per_item_avg: Mapped[float | None] = mapped_column(
        Numeric(6, 2), nullable=True
    )
    hint_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    abandon_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metrics_version: Mapped[str] = mapped_column(
        String(20), default="V1", nullable=False
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )


class MasteryState(Base):
    __tablename__ = "mastery_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", name="mastery_states_student_id_fkey"),
        nullable=False,
    )
    microconcept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("microconcepts.id", name="mastery_states_microconcept_id_fkey"),
        nullable=False,
    )
    mastery_score: Mapped[float] = mapped_column(
        Numeric(6, 4), default=0.0, nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("dominant", "in_progress", "at_risk", name="mastery_status"),
        default="in_progress",
        nullable=False,
    )
    last_practice_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    recommended_next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metrics_version: Mapped[str] = mapped_column(
        String(20), default="V1", nullable=False
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )
