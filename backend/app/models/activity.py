import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ActivityType(Base):
    __tablename__ = "activity_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )


class ActivitySession(Base):
    __tablename__ = "activity_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", name="activity_sessions_student_id_fkey"),
        nullable=False,
    )
    activity_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_types.id", name="activity_sessions_activity_type_id_fkey"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", name="activity_sessions_subject_id_fkey"),
        nullable=False,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.id", name="activity_sessions_term_id_fkey"),
        nullable=False,
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", name="activity_sessions_topic_id_fkey"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="in_progress", nullable=False
    )  # in_progress, completed, abandoned
    feedback_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )


class ActivitySessionItem(Base):
    __tablename__ = "activity_session_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_sessions.id", name="activity_session_items_session_id_fkey"),
        nullable=False,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id", name="activity_session_items_item_id_fkey"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    presented_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", name="learning_events_student_id_fkey"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_sessions.id", name="learning_events_session_id_fkey"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", name="learning_events_subject_id_fkey"),
        nullable=False,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.id", name="learning_events_term_id_fkey"),
        nullable=False,
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", name="learning_events_topic_id_fkey"),
        nullable=True,
    )
    microconcept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("microconcepts.id", name="learning_events_microconcept_id_fkey"),
        nullable=True,
    )
    activity_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity_types.id", name="learning_events_activity_type_id_fkey"),
        nullable=False,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id", name="learning_events_item_id_fkey"),
        nullable=False,
    )
    timestamp_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    timestamp_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    response_normalized: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    hint_used: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # none, hint, explanation, theory
    difficulty_at_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )
