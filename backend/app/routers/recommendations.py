import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.recommendation import RecommendationInstance
from app.models.student import Student
from app.models.tutor import Tutor
from app.schemas.recommendation import (
    RecommendationInstanceResponse,
    TutorDecisionCreate,
    TutorDecisionResponse,
)
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Note: In a real app we'd get current_tutor from auth dependency
# For MVP Sprint 1 we might pass tutor_id in body or header or mock it


@router.get("/students/{student_id}", response_model=List[RecommendationInstanceResponse])
def get_student_recommendations(
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    status_filter: str = "pending",  # pending, accepted, rejected, all
    generate: bool = True,  # If true, run generation logic
    db: Session = Depends(get_db),
):
    """
    Get recommendations for a student.
    By default runs generation logic to find new recommendations based on latest metrics.
    """
    student = db.query(Student).get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if generate:
        # Run generation logic
        recommendation_service.generate_recommendations(db, student_id, subject_id, term_id)

    query = db.query(RecommendationInstance).filter(RecommendationInstance.student_id == student_id)

    if status_filter != "all":
        query = query.filter(RecommendationInstance.status == status_filter)

    recommendations = query.order_by(
        RecommendationInstance.priority,
        RecommendationInstance.generated_at.desc(),
    ).all()
    return recommendations


@router.get("/{recommendation_id}", response_model=RecommendationInstanceResponse)
def get_recommendation(recommendation_id: uuid.UUID, db: Session = Depends(get_db)):
    rec = db.query(RecommendationInstance).get(recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.post("/{recommendation_id}/decision", response_model=TutorDecisionResponse)
def make_tutor_decision(
    recommendation_id: uuid.UUID, decision: TutorDecisionCreate, db: Session = Depends(get_db)
):
    """
    Record tutor decision (accept/reject) on a recommendation.
    """
    # Verify tutor exists
    tutor = db.query(Tutor).get(decision.tutor_id)
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")

    try:
        if decision.recommendation_id != recommendation_id:
            # Basic validation
            raise ValueError("Recommendation ID mismatch")

        result = recommendation_service.apply_tutor_decision(db, decision)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
