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
    microconcept_id: Optional[uuid.UUID] = None
    rule_id: str
    priority: str
    status: str
    title: str
    description: str


class RecommendationInstanceCreate(RecommendationInstanceBase):
    evidence_list: List[RecommendationEvidenceCreate]


class RecommendationInstanceResponse(RecommendationInstanceBase):
    id: uuid.UUID
    generated_at: datetime
    updated_at: datetime
    evidence: List[RecommendationEvidenceResponse]
    decision: Optional[TutorDecisionResponse] = None

    class Config:
        from_attributes = True
