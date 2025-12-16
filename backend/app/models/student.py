import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("user_id", name="students_user_id_key"),
        Index("idx_students_user", "user_id"),
        Index("idx_students_subject", "subject_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", name="students_user_id_fkey"), nullable=True
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", name="students_subject_id_fkey"),
        nullable=True,
    )
    enrollment_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )
