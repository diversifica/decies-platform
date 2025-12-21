import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LLMRunStep(str, enum.Enum):
    E2_STRUCTURE = "E2_STRUCTURE"
    E3_MAP = "E3_MAP"
    E4_ITEMS = "E4_ITEMS"
    E5_VALIDATE = "E5_VALIDATE"


class LLMRun(Base):
    __tablename__ = "llm_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_upload_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "content_uploads.id",
            name="llm_runs_content_upload_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=True,
    )
    knowledge_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "knowledge_entries.id",
            name="llm_runs_knowledge_entry_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    knowledge_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "knowledge_chunks.id",
            name="llm_runs_knowledge_chunk_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    step: Mapped[LLMRunStep] = mapped_column(
        Enum(LLMRunStep, name="llm_run_step", create_type=False), nullable=False
    )
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    subfolder: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Context identifier
    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    prompt_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="V1",
        server_default=text("'V1'"),
    )
    engine_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="V1",
        server_default=text("'V1'"),
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )
