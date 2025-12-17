import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TutorReportSectionResponse(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    order_index: int
    section_type: str
    title: str
    content: str
    data: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class TutorReportResponse(BaseModel):
    id: uuid.UUID
    tutor_id: uuid.UUID
    student_id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID
    summary: str
    metrics_snapshot: dict[str, Any] | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    generated_at: datetime
    sections: list[TutorReportSectionResponse] = []

    model_config = ConfigDict(from_attributes=True)
