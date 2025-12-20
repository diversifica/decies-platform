import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AssessmentScopeTagBase(BaseModel):
    topic_id: uuid.UUID | None = None
    microconcept_id: uuid.UUID | None = None
    weight: float | None = None


class AssessmentScopeTagCreate(AssessmentScopeTagBase):
    pass


class AssessmentScopeTagResponse(AssessmentScopeTagBase):
    id: uuid.UUID
    real_grade_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class RealGradeBase(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID
    assessment_date: date
    grade_value: float = Field(..., ge=0)
    grading_scale: str | None = None
    notes: str | None = None


class RealGradeCreate(RealGradeBase):
    scope_tags: list[AssessmentScopeTagCreate] = []


class RealGradeUpdate(BaseModel):
    assessment_date: date | None = None
    grade_value: float | None = Field(default=None, ge=0)
    grading_scale: str | None = None
    notes: str | None = None


class RealGradeResponse(RealGradeBase):
    id: uuid.UUID
    created_by_tutor_id: uuid.UUID
    created_at: datetime | None = None
    scope_tags: list[AssessmentScopeTagResponse] = []

    model_config = ConfigDict(from_attributes=True)
