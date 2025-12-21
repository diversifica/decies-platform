import uuid
from datetime import datetime

from pydantic import BaseModel


class MetricAggregateBase(BaseModel):
    student_id: uuid.UUID
    scope_type: str  # subject, term, topic, microconcept, activity_type
    scope_id: uuid.UUID
    window_start: datetime
    window_end: datetime
    accuracy: float | None = None
    first_attempt_accuracy: float | None = None
    error_rate: float | None = None
    median_response_time_ms: int | None = None
    attempts_per_item_avg: float | None = None
    hint_rate: float | None = None
    abandon_rate: float | None = None
    metrics_version: str = "V1"


class MetricAggregateCreate(MetricAggregateBase):
    computed_at: datetime


class MetricAggregateResponse(MetricAggregateBase):
    id: uuid.UUID
    computed_at: datetime
    created_at: datetime | None

    class Config:
        from_attributes = True


class MasteryStateBase(BaseModel):
    student_id: uuid.UUID
    microconcept_id: uuid.UUID
    mastery_score: float
    status: str  # dominant, in_progress, at_risk
    last_practice_at: datetime | None = None
    recommended_next_review_at: datetime | None = None
    metrics_version: str = "V1"


class MasteryStateCreate(MasteryStateBase):
    updated_at: datetime


class MasteryStateResponse(MasteryStateBase):
    id: uuid.UUID
    updated_at: datetime
    created_at: datetime | None

    class Config:
        from_attributes = True


class StudentMetricsSummary(BaseModel):
    """Summary of student metrics for dashboard"""

    student_id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID
    accuracy: float | None
    first_attempt_accuracy: float | None
    median_response_time_ms: int | None
    hint_rate: float | None
    total_sessions: int
    total_items_completed: int
    window_start: datetime
    window_end: datetime


class MasteryStateSummary(BaseModel):
    """Summary of mastery state for a microconcept"""

    microconcept_id: uuid.UUID
    microconcept_name: str
    mastery_score: float
    status: str
    last_practice_at: datetime | None
    recommended_next_review_at: datetime | None = None
    total_events: int
