import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SubjectSummary(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TermSummary(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    status: str
    start_date: date | None = None
    end_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentSummary(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    enrollment_date: datetime | None = None
    email: str | None = None
    full_name: str | None = None


class TopicSummary(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID | None = None
    code: str | None = None
    name: str

    model_config = ConfigDict(from_attributes=True)
