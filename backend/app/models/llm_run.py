import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LLMRunStep(str, enum.Enum):
    E2_STRUCTURE = "E2_STRUCTURE"
    E3_MAP = "E3_MAP"
    E4_ITEMS = "E4_ITEMS"


class LLMRun(Base):
    __tablename__ = "llm_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step: Mapped[LLMRunStep] = mapped_column(
        Enum(LLMRunStep, name="llm_run_step", create_type=False), nullable=False
    )
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    subfolder: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Context identifier
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, failed
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )
