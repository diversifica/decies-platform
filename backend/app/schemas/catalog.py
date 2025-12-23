import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, constr


class SubjectSummary(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255)
    description: str | None = None


class SubjectUpdate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255) | None = None
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TermSummary(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    status: str
    academic_year_name: str | None = None
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


class StudentSubjectUpdate(BaseModel):
    subject_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class TopicSummary(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID | None = None
    code: str | None = None
    name: str

    model_config = ConfigDict(from_attributes=True)
