import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user, get_current_role_name, get_current_student
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
from app.models.subject import Subject
from app.models.user import User
from app.schemas.metric import (
    MasteryStateSummary,
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
    current_user: User = Depends(get_current_active_user),
):
    """
    Get aggregated metrics for a student in a subject/term.
    """
    role_name = get_current_role_name(db, current_user)
    if role_name == "student":
        student = get_current_student(db=db, current_user=current_user)
        if student_id != student.id:
            raise HTTPException(status_code=403, detail="Not allowed")
        if student.subject_id and student.subject_id != subject_id:
            raise HTTPException(status_code=403, detail="Not allowed")
    elif role_name == "tutor":
        subject = db.get(Subject, subject_id)
        if subject and subject.tutor_id and subject.tutor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    else:
        raise HTTPException(status_code=403, detail="Role not allowed")

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
        metric = metric_service.calculate_student_metrics(db, student_id, subject_id, term_id)
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

    error_rate = metric.error_rate
    if error_rate is None and metric.accuracy is not None:
        error_rate = round(1.0 - float(metric.accuracy), 4)

    performance_consistency = None
    session_rows = (
        db.query(ActivitySession.id)
        .filter(
            ActivitySession.student_id == student_id,
            ActivitySession.subject_id == subject_id,
            ActivitySession.term_id == term_id,
            ActivitySession.started_at >= metric.window_start,
        )
        .all()
    )
    session_ids = [row[0] for row in session_rows]
    if session_ids:
        events = (
            db.query(LearningEvent.session_id, LearningEvent.is_correct)
            .filter(LearningEvent.session_id.in_(session_ids))
            .all()
        )
        by_session: dict[uuid.UUID, list[bool]] = {}
        for sid, is_correct in events:
            by_session.setdefault(sid, []).append(bool(is_correct))
        per_session_acc: list[float] = []
        for values in by_session.values():
            if len(values) < 3:
                continue
            per_session_acc.append(sum(1 for v in values if v) / len(values))
        if len(per_session_acc) >= 2:
            mean = sum(per_session_acc) / len(per_session_acc)
            variance = sum((x - mean) ** 2 for x in per_session_acc) / len(per_session_acc)
            performance_consistency = round(variance**0.5, 4)

    return StudentMetricsSummary(
        student_id=student_id,
        subject_id=subject_id,
        term_id=term_id,
        accuracy=metric.accuracy,
        first_attempt_accuracy=metric.first_attempt_accuracy,
        error_rate=error_rate,
        performance_consistency=performance_consistency,
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
    current_user: User = Depends(get_current_active_user),
):
    """
    Get mastery states for all microconcepts for a student.
    """
    role_name = get_current_role_name(db, current_user)
    if role_name == "student":
        student = get_current_student(db=db, current_user=current_user)
        if student_id != student.id:
            raise HTTPException(status_code=403, detail="Not allowed")
        if student.subject_id and student.subject_id != subject_id:
            raise HTTPException(status_code=403, detail="Not allowed")
    elif role_name == "tutor":
        subject = db.get(Subject, subject_id)
        if subject and subject.tutor_id and subject.tutor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    else:
        raise HTTPException(status_code=403, detail="Role not allowed")

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
                LearningEvent.subject_id == subject_id,
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
                recommended_next_review_at=ms.recommended_next_review_at,
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
    current_user: User = Depends(get_current_active_user),
):
    """
    Manually trigger metrics recalculation (admin/debug endpoint).
    """
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")
    subject = db.get(Subject, subject_id)
    if subject and subject.tutor_id and subject.tutor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

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
