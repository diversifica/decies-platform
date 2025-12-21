import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RecommendationEvidenceBase(BaseModel):
    evidence_type: str
    key: str
    value: str
    description: Optional[str] = None


class RecommendationEvidenceCreate(RecommendationEvidenceBase):
    pass


class RecommendationEvidenceResponse(RecommendationEvidenceBase):
    id: uuid.UUID
    recommendation_id: uuid.UUID

    class Config:
        from_attributes = True


class TutorDecisionBase(BaseModel):
    decision: str  # accepted, rejected
    notes: Optional[str] = None


class TutorDecisionCreate(TutorDecisionBase):
    tutor_id: uuid.UUID
    recommendation_id: uuid.UUID


class TutorDecisionResponse(TutorDecisionBase):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    tutor_id: uuid.UUID
    decision_at: datetime

    class Config:
        from_attributes = True


class RecommendationInstanceBase(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID | None = None
    term_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    microconcept_id: Optional[uuid.UUID] = None
    rule_id: str
    recommendation_code: str | None = None
    category: Optional[str] = None
    catalog_version: str | None = None
    priority: str
    status: str
    engine_version: str
    ruleset_version: str
    title: str
    description: str


class RecommendationInstanceCreate(RecommendationInstanceBase):
    evidence_list: List[RecommendationEvidenceCreate]


class RecommendationOutcomeResponse(BaseModel):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    evaluation_start: datetime
    evaluation_end: datetime
    success: str
    delta_mastery: float | None = None
    delta_retention: float | None = None
    delta_accuracy: float | None = None
    delta_hint_rate: float | None = None
    engine_version: str
    ruleset_version: str
    computed_at: datetime
    notes: str | None = None

    class Config:
        from_attributes = True


class RecommendationInstanceResponse(RecommendationInstanceBase):
    id: uuid.UUID
    generated_at: datetime
    updated_at: datetime
    evidence: List[RecommendationEvidenceResponse]
    decision: Optional[TutorDecisionResponse] = None
    outcome: Optional[RecommendationOutcomeResponse] = None

    class Config:
        from_attributes = True


class RecommendationOutcomeComputeResponse(BaseModel):
    outcomes: list[RecommendationOutcomeResponse]
    created: int
    updated: int
    pending: int
