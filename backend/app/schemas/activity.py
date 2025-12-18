import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ActivityTypeBase(BaseModel):
    code: str
    name: str
    active: bool = True


class ActivityTypeCreate(ActivityTypeBase):
    pass


class ActivityTypeResponse(ActivityTypeBase):
    id: uuid.UUID
    created_at: datetime | None

    class Config:
        from_attributes = True


class ActivitySessionBase(BaseModel):
    student_id: uuid.UUID
    activity_type_id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID
    topic_id: uuid.UUID | None = None
    device_type: str | None = None


class ActivitySessionCreate(ActivitySessionBase):
    item_count: int = 10  # Number of items to include in session
    content_upload_id: uuid.UUID | None = None


class ActivitySessionFeedbackCreate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ActivitySessionResponse(ActivitySessionBase):
    id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    status: str
    created_at: datetime | None

    class Config:
        from_attributes = True


class ActivitySessionItemBase(BaseModel):
    session_id: uuid.UUID
    item_id: uuid.UUID
    order_index: int


class ActivitySessionItemResponse(ActivitySessionItemBase):
    id: uuid.UUID
    presented_at: datetime | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class LearningEventBase(BaseModel):
    student_id: uuid.UUID
    # session_id removed from base, provided via path param for creation
    item_id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID
    topic_id: uuid.UUID | None = None
    microconcept_id: uuid.UUID | None = None
    activity_type_id: uuid.UUID
    is_correct: bool
    duration_ms: int
    attempt_number: int = 1
    response_normalized: str | None = None
    hint_used: str | None = None
    difficulty_at_time: int | None = None


class LearningEventCreate(LearningEventBase):
    timestamp_start: datetime
    timestamp_end: datetime


class LearningEventResponse(LearningEventBase):
    id: uuid.UUID
    session_id: uuid.UUID
    timestamp_start: datetime
    timestamp_end: datetime
    created_at: datetime | None

    class Config:
        from_attributes = True
