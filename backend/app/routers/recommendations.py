import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_active_user, get_current_role_name, get_current_tutor
from app.models.recommendation import RecommendationInstance
from app.models.recommendation_catalog import RecommendationCatalog
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationInstanceResponse,
    RecommendationOutcomeComputeResponse,
    TutorDecisionCreate,
    TutorDecisionResponse,
)
from app.services.recommendation_outcome_service import recommendation_outcome_service
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
    current_user: User = Depends(get_current_active_user),
):
    """
    Get recommendations for a student.
    By default runs generation logic to find new recommendations based on latest metrics.
    """
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")
    get_current_tutor(db=db, current_user=current_user)

    subject = db.get(Subject, subject_id)
    if subject and subject.tutor_id and subject.tutor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.subject_id and student.subject_id != subject_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if generate:
        # Run generation logic
        recommendation_service.generate_recommendations(db, student_id, subject_id, term_id)

    query = (
        db.query(RecommendationInstance)
        .options(
            selectinload(RecommendationInstance.evidence),
            selectinload(RecommendationInstance.decision),
            selectinload(RecommendationInstance.outcome),
        )
        .filter(RecommendationInstance.student_id == student_id)
        .filter(
            or_(
                RecommendationInstance.subject_id == subject_id,
                RecommendationInstance.subject_id.is_(None),
            )
        )
        .filter(
            or_(
                RecommendationInstance.term_id == term_id,
                RecommendationInstance.term_id.is_(None),
            )
        )
    )

    if status_filter != "all":
        query = query.filter(RecommendationInstance.status == status_filter)

    recommendations = query.order_by(
        RecommendationInstance.priority,
        RecommendationInstance.generated_at.desc(),
    ).all()

    codes = {r.rule_id for r in recommendations}
    if codes:
        catalog_rows = (
            db.query(RecommendationCatalog.code, RecommendationCatalog.category)
            .filter(RecommendationCatalog.code.in_(codes))
            .all()
        )
        category_by_code = {code: category for code, category in catalog_rows}
        for rec in recommendations:
            setattr(rec, "category", category_by_code.get(rec.rule_id))
    return recommendations


@router.get("/{recommendation_id}", response_model=RecommendationInstanceResponse)
def get_recommendation(
    recommendation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")

    rec = (
        db.query(RecommendationInstance)
        .options(
            selectinload(RecommendationInstance.evidence),
            selectinload(RecommendationInstance.decision),
            selectinload(RecommendationInstance.outcome),
        )
        .filter(RecommendationInstance.id == recommendation_id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    category = (
        db.query(RecommendationCatalog.category)
        .filter(RecommendationCatalog.code == rec.rule_id)
        .scalar()
    )
    setattr(rec, "category", category)

    student = db.get(Student, rec.student_id)
    if student and student.subject_id:
        subject = db.get(Subject, student.subject_id)
        if subject and subject.tutor_id and subject.tutor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    return rec


@router.post("/{recommendation_id}/decision", response_model=TutorDecisionResponse)
def make_tutor_decision(
    recommendation_id: uuid.UUID,
    decision: TutorDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record tutor decision (accept/reject) on a recommendation.
    """
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")
    tutor = get_current_tutor(db=db, current_user=current_user)
    if decision.tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Tutor mismatch")

    rec = db.get(RecommendationInstance, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    student = db.get(Student, rec.student_id)
    if student and student.subject_id:
        subject = db.get(Subject, student.subject_id)
        if subject and subject.tutor_id and subject.tutor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

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


@router.post("/outcomes/compute", response_model=RecommendationOutcomeComputeResponse)
def compute_recommendation_outcomes(
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")

    tutor = get_current_tutor(db=db, current_user=current_user)

    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.tutor_id and subject.tutor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if not db.get(Term, term_id):
        raise HTTPException(status_code=404, detail="Term not found")

    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.subject_id and student.subject_id != subject_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    outcomes, created, updated, pending = recommendation_outcome_service.compute_outcomes(
        db,
        tutor_id=tutor.id,
        student_id=student_id,
        subject_id=subject_id,
        term_id=term_id,
        force=force,
    )

    return {
        "outcomes": outcomes,
        "created": created,
        "updated": updated,
        "pending": pending,
    }
