import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.core.versioning import RECOMMENDATION_ENGINE_VERSION, RECOMMENDATION_RULESET_VERSION
from app.models.activity import LearningEvent
from app.models.microconcept import MicroConcept
from app.models.recommendation import (
    RecommendationInstance,
    RecommendationOutcome,
    RecommendationStatus,
)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_window_metrics(
    db: Session,
    *,
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    window_start: datetime,
    window_end: datetime,
) -> dict[str, float]:
    events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.student_id == student_id,
            LearningEvent.subject_id == subject_id,
            LearningEvent.term_id == term_id,
            LearningEvent.timestamp_start >= window_start,
            LearningEvent.timestamp_start < window_end,
        )
        .all()
    )

    if not events:
        return {"accuracy": 0.0, "hint_rate": 0.0}

    total = len(events)
    correct = sum(1 for e in events if e.is_correct)
    hint = sum(1 for e in events if e.hint_used and e.hint_used != "none")

    return {
        "accuracy": correct / total if total else 0.0,
        "hint_rate": hint / total if total else 0.0,
    }


def _compute_microconcept_mastery_at(
    db: Session,
    *,
    student_id: uuid.UUID,
    microconcept_id: uuid.UUID,
    now: datetime,
) -> float:
    events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.student_id == student_id,
            LearningEvent.microconcept_id == microconcept_id,
            LearningEvent.timestamp_start <= now,
        )
        .order_by(LearningEvent.timestamp_start.desc())
        .all()
    )
    if not events:
        return 0.0

    total = len(events)
    correct = sum(1 for e in events if e.is_correct)
    hint = sum(1 for e in events if e.hint_used and e.hint_used != "none")

    accuracy = correct / total if total else 0.0
    hint_rate = hint / total if total else 0.0

    last_practice = events[0].timestamp_start
    days_since_practice = (now - last_practice).days
    recency_factor = max(0.5, 1.0 - (days_since_practice / 30.0))

    mastery_score = accuracy * (1.0 - hint_rate) * recency_factor
    return round(mastery_score, 6)


def _compute_subject_mastery_at(
    db: Session,
    *,
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    now: datetime,
) -> float:
    microconcept_ids = [
        mc.id
        for mc in db.query(MicroConcept)
        .filter(
            MicroConcept.subject_id == subject_id,
            MicroConcept.term_id == term_id,
            MicroConcept.active == True,  # noqa: E712
        )
        .all()
    ]
    if not microconcept_ids:
        return 0.0

    scores = [
        _compute_microconcept_mastery_at(
            db,
            student_id=student_id,
            microconcept_id=microconcept_id,
            now=now,
        )
        for microconcept_id in microconcept_ids
    ]
    return round(sum(scores) / len(scores), 6)


def _classify_success(delta_mastery: float | None, delta_accuracy: float | None) -> str:
    mastery = delta_mastery if delta_mastery is not None else 0.0
    accuracy = delta_accuracy if delta_accuracy is not None else 0.0

    if mastery >= 0.05 or accuracy >= 0.05:
        return "true"
    if mastery <= -0.05 and accuracy <= -0.05:
        return "false"
    return "partial"


class RecommendationOutcomeService:
    def compute_outcomes(
        self,
        db: Session,
        *,
        tutor_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
        force: bool = False,
        now: datetime | None = None,
    ) -> tuple[list[RecommendationOutcome], int, int, int]:
        """
        Computes outcomes for accepted recommendations belonging to a tutor.

        Returns: (upserted_outcomes, created_count, updated_count, pending_count)
        """
        now = now or datetime.utcnow()

        recommendations = (
            db.query(RecommendationInstance)
            .options(
                selectinload(RecommendationInstance.decision),
                selectinload(RecommendationInstance.outcome),
            )
            .filter(
                RecommendationInstance.student_id == student_id,
                RecommendationInstance.status == RecommendationStatus.ACCEPTED,
                or_(
                    RecommendationInstance.subject_id == subject_id,
                    RecommendationInstance.subject_id.is_(None),
                ),
                or_(
                    RecommendationInstance.term_id == term_id,
                    RecommendationInstance.term_id.is_(None),
                ),
            )
            .all()
        )

        upserted: list[RecommendationOutcome] = []
        created = 0
        updated = 0
        pending = 0

        for rec in recommendations:
            decision = rec.decision
            if not decision or decision.decision != "accepted" or decision.tutor_id != tutor_id:
                continue

            evaluation_start = decision.decision_at
            window_days = rec.evaluation_window_days or 14
            evaluation_end = evaluation_start + timedelta(days=window_days)

            if evaluation_end > now:
                pending += 1
                continue

            if rec.outcome and not force:
                continue

            pre_start = evaluation_start - timedelta(days=window_days)
            pre = _compute_window_metrics(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                window_start=pre_start,
                window_end=evaluation_start,
            )
            post = _compute_window_metrics(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                window_start=evaluation_start,
                window_end=evaluation_end,
            )

            delta_accuracy = post["accuracy"] - pre["accuracy"]
            delta_hint_rate = post["hint_rate"] - pre["hint_rate"]

            if rec.microconcept_id:
                mastery_start = _compute_microconcept_mastery_at(
                    db,
                    student_id=student_id,
                    microconcept_id=rec.microconcept_id,
                    now=evaluation_start,
                )
                mastery_end = _compute_microconcept_mastery_at(
                    db,
                    student_id=student_id,
                    microconcept_id=rec.microconcept_id,
                    now=evaluation_end,
                )
            else:
                mastery_start = _compute_subject_mastery_at(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    now=evaluation_start,
                )
                mastery_end = _compute_subject_mastery_at(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    now=evaluation_end,
                )

            delta_mastery = mastery_end - mastery_start
            success = _classify_success(delta_mastery, delta_accuracy)

            if rec.outcome:
                outcome = rec.outcome
                outcome.evaluation_start = evaluation_start
                outcome.evaluation_end = evaluation_end
                outcome.success = success
                outcome.delta_mastery = delta_mastery
                outcome.delta_accuracy = delta_accuracy
                outcome.delta_hint_rate = delta_hint_rate
                outcome.engine_version = rec.engine_version or RECOMMENDATION_ENGINE_VERSION
                outcome.ruleset_version = rec.ruleset_version or RECOMMENDATION_RULESET_VERSION
                outcome.computed_at = now
                db.add(outcome)
                updated += 1
            else:
                outcome = RecommendationOutcome(
                    id=uuid.uuid4(),
                    recommendation_id=rec.id,
                    evaluation_start=evaluation_start,
                    evaluation_end=evaluation_end,
                    success=success,
                    delta_mastery=delta_mastery,
                    delta_accuracy=delta_accuracy,
                    delta_hint_rate=delta_hint_rate,
                    engine_version=rec.engine_version or RECOMMENDATION_ENGINE_VERSION,
                    ruleset_version=rec.ruleset_version or RECOMMENDATION_RULESET_VERSION,
                    computed_at=now,
                    notes=None,
                )
                db.add(outcome)
                created += 1

            upserted.append(outcome)

        db.commit()
        for outcome in upserted:
            db.refresh(outcome)

        return upserted, created, updated, pending


recommendation_outcome_service = RecommendationOutcomeService()
