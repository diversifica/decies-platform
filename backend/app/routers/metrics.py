import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
from app.schemas.metric import (
    MasteryStateSummary,
    MetricAggregateResponse,
    StudentMetricsSummary,
)
from app.services.metric_service import metric_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/students/{student_id}/metrics", response_model=StudentMetricsSummary)
def get_student_metrics(
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Get aggregated metrics for a student in a subject/term.
    """
    # Get latest metric aggregate
    metric = (
        db.query(MetricAggregate)
        .filter(
            MetricAggregate.student_id == student_id,
            MetricAggregate.scope_type == "subject",
            MetricAggregate.scope_id == subject_id,
        )
        .order_by(MetricAggregate.computed_at.desc())
        .first()
    )

    if not metric:
        # Calculate metrics if not exists
        metric = metric_service.calculate_student_metrics(
            db, student_id, subject_id, term_id
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)

    # Count sessions and items (simplified for MVP)
    from app.models.activity import ActivitySession, LearningEvent

    total_sessions = (
        db.query(ActivitySession)
        .filter(
            ActivitySession.student_id == student_id,
            ActivitySession.subject_id == subject_id,
            ActivitySession.status == "completed",
        )
        .count()
    )

    total_items = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.student_id == student_id,
            LearningEvent.subject_id == subject_id,
        )
        .count()
    )

    return StudentMetricsSummary(
        student_id=student_id,
        subject_id=subject_id,
        term_id=term_id,
        accuracy=metric.accuracy,
        first_attempt_accuracy=metric.first_attempt_accuracy,
        median_response_time_ms=metric.median_response_time_ms,
        hint_rate=metric.hint_rate,
        total_sessions=total_sessions,
        total_items_completed=total_items,
        window_start=metric.window_start,
        window_end=metric.window_end,
    )


@router.get("/students/{student_id}/mastery", response_model=list[MasteryStateSummary])
def get_student_mastery(
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Get mastery states for all microconcepts for a student.
    """
    # Get mastery states
    mastery_states = (
        db.query(MasteryState)
        .filter(MasteryState.student_id == student_id)
        .join(MicroConcept, MasteryState.microconcept_id == MicroConcept.id)
        .filter(
            MicroConcept.subject_id == subject_id,
            MicroConcept.term_id == term_id,
        )
        .all()
    )

    if not mastery_states:
        # Calculate mastery states if not exists
        mastery_states = metric_service.calculate_mastery_states(
            db, student_id, subject_id, term_id
        )
        for ms in mastery_states:
            db.add(ms)
        db.commit()

    # Build summary with microconcept names
    summaries = []
    for ms in mastery_states:
        mc = db.query(MicroConcept).filter_by(id=ms.microconcept_id).first()
        if not mc:
            continue

        # Count events for this microconcept
        from app.models.activity import LearningEvent

        event_count = (
            db.query(LearningEvent)
            .filter(
                LearningEvent.student_id == student_id,
                LearningEvent.microconcept_id == ms.microconcept_id,
            )
            .count()
        )

        summaries.append(
            MasteryStateSummary(
                microconcept_id=ms.microconcept_id,
                microconcept_name=mc.name,
                mastery_score=ms.mastery_score,
                status=ms.status,
                last_practice_at=ms.last_practice_at,
                total_events=event_count,
            )
        )

    return summaries


@router.post("/recalculate")
def recalculate_metrics(
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Manually trigger metrics recalculation (admin/debug endpoint).
    """
    try:
        metrics, mastery_states = metric_service.recalculate_and_save_metrics(
            db, student_id, subject_id, term_id
        )

        return {
            "status": "success",
            "metrics_id": str(metrics.id),
            "mastery_states_count": len(mastery_states),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")
