import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RecommendationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationInstance(Base):
    __tablename__ = "recommendation_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "students.id",
            name="recommendation_instances_student_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Optional: Recommendations can be specific to a microconcept, topic, subject, etc.
    microconcept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "microconcepts.id",
            name="recommendation_instances_microconcept_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    rule_id: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "R01", "R11"
    priority: Mapped[RecommendationPriority] = mapped_column(
        Enum(RecommendationPriority, name="recommendation_priority", create_type=False),
        nullable=False,
        default=RecommendationPriority.MEDIUM,
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, name="recommendation_status", create_type=False),
        nullable=False,
        default=RecommendationStatus.PENDING,
    )

    title: Mapped[str] = mapped_column(String, nullable=False)  # Human readable title
    description: Mapped[str] = mapped_column(Text, nullable=False)  # Description of what to do

    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    evidence: Mapped[list["RecommendationEvidence"]] = relationship(
        "RecommendationEvidence",
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )
    decision: Mapped["TutorDecision"] = relationship(
        "TutorDecision",
        back_populates="recommendation",
        uselist=False,
        cascade="all, delete-orphan",
    )


class RecommendationEvidence(Base):
    __tablename__ = "recommendation_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "recommendation_instances.id",
            name="recommendation_evidence_recommendation_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    evidence_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # e.g., "metric_value", "history_pattern"
    key: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "accuracy", "attempts"
    value: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "0.45", "3"
    description: Mapped[str] = mapped_column(String, nullable=True)  # Human readable text

    recommendation: Mapped["RecommendationInstance"] = relationship(
        "RecommendationInstance", back_populates="evidence"
    )


class TutorDecision(Base):
    __tablename__ = "tutor_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "recommendation_instances.id",
            name="tutor_decisions_recommendation_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )
    tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id", name="tutor_decisions_tutor_id_fkey", ondelete="CASCADE"),
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "accepted", "rejected" - mirroring status mostly
    decision_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    recommendation: Mapped["RecommendationInstance"] = relationship(
        "RecommendationInstance", back_populates="decision"
    )
