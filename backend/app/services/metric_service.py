import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.activity import LearningEvent
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept


class MetricService:
    """Service for calculating student metrics and mastery states"""

    def _compute_recommended_next_review_at(
        self,
        *,
        now: datetime,
        last_practice_at: datetime | None,
        status: str,
        mastery_score: float,
    ) -> datetime:
        if last_practice_at is None:
            return now

        status_key = (status or "").casefold()
        if status_key == "dominant":
            interval_days = 14
        elif status_key == "in_progress":
            interval_days = 7
        else:
            interval_days = 2

        if mastery_score < 0.2:
            interval_days = min(interval_days, 1)
        elif mastery_score >= 0.9:
            interval_days = max(interval_days, 21)

        return last_practice_at + timedelta(days=interval_days)

    def calculate_student_metrics(
        self,
        db: Session,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
        window_days: int = 30,
    ) -> MetricAggregate:
        """
        Calculate aggregated metrics for a student in a given subject/term.

        Returns a MetricAggregate with:
        - accuracy: % of correct responses
        - first_attempt_accuracy: % correct on first attempt
        - median_response_time_ms: median time to respond
        - hint_rate: % of events where hints were used
        """
        window_start = datetime.utcnow() - timedelta(days=window_days)
        window_end = datetime.utcnow()

        # Get all learning events in the window
        events = (
            db.query(LearningEvent)
            .filter(
                LearningEvent.student_id == student_id,
                LearningEvent.subject_id == subject_id,
                LearningEvent.term_id == term_id,
                LearningEvent.timestamp_start >= window_start,
            )
            .all()
        )

        if not events:
            # No events, return zero metrics
            return MetricAggregate(
                student_id=student_id,
                scope_type="subject",
                scope_id=subject_id,
                window_start=window_start,
                window_end=window_end,
                accuracy=0.0,
                first_attempt_accuracy=0.0,
                error_rate=1.0,
                median_response_time_ms=0,
                attempts_per_item_avg=0.0,
                hint_rate=0.0,
                computed_at=datetime.utcnow(),
            )

        # Calculate metrics
        total_events = len(events)
        correct_events = sum(1 for e in events if e.is_correct)
        first_attempt_events = [e for e in events if e.attempt_number == 1]
        first_attempt_correct = sum(1 for e in first_attempt_events if e.is_correct)
        hint_events = sum(1 for e in events if e.hint_used and e.hint_used != "none")

        accuracy = correct_events / total_events if total_events > 0 else 0.0
        first_attempt_accuracy = (
            first_attempt_correct / len(first_attempt_events) if first_attempt_events else 0.0
        )
        error_rate = 1.0 - accuracy
        hint_rate = hint_events / total_events if total_events > 0 else 0.0

        # Calculate median response time
        response_times = sorted([e.duration_ms for e in events])
        median_idx = len(response_times) // 2
        median_response_time_ms = response_times[median_idx] if response_times else 0

        # Calculate average attempts per item
        item_attempts = {}
        for e in events:
            item_id = str(e.item_id)
            if item_id not in item_attempts:
                item_attempts[item_id] = 0
            item_attempts[item_id] += 1

        attempts_per_item_avg = (
            sum(item_attempts.values()) / len(item_attempts) if item_attempts else 0.0
        )

        return MetricAggregate(
            student_id=student_id,
            scope_type="subject",
            scope_id=subject_id,
            window_start=window_start,
            window_end=window_end,
            accuracy=round(accuracy, 4),
            first_attempt_accuracy=round(first_attempt_accuracy, 4),
            error_rate=round(error_rate, 4),
            median_response_time_ms=median_response_time_ms,
            attempts_per_item_avg=round(attempts_per_item_avg, 2),
            hint_rate=round(hint_rate, 4),
            computed_at=datetime.utcnow(),
        )

    def calculate_mastery_states(
        self,
        db: Session,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
    ) -> list[MasteryState]:
        """
        Calculate mastery states for all microconcepts in a subject/term.

        Mastery score algorithm (simple V1):
        mastery_score = accuracy * (1 - hint_rate) * recency_factor

        Status thresholds:
        - dominant: mastery_score >= 0.8
        - in_progress: 0.5 <= mastery_score < 0.8
        - at_risk: mastery_score < 0.5
        """
        now = datetime.utcnow()
        # Get all microconcepts for this subject/term
        microconcepts = (
            db.query(MicroConcept)
            .filter(
                MicroConcept.subject_id == subject_id,
                MicroConcept.term_id == term_id,
                MicroConcept.active == True,  # noqa: E712
            )
            .all()
        )

        mastery_states = []

        for mc in microconcepts:
            # Get learning events for this microconcept
            events = (
                db.query(LearningEvent)
                .filter(
                    LearningEvent.student_id == student_id,
                    LearningEvent.microconcept_id == mc.id,
                )
                .order_by(LearningEvent.timestamp_start.desc())
                .all()
            )

            if not events:
                # No practice yet, create default state
                status = "at_risk"
                mastery_score = 0.0
                mastery_states.append(
                    MasteryState(
                        student_id=student_id,
                        microconcept_id=mc.id,
                        mastery_score=mastery_score,
                        status=status,
                        last_practice_at=None,
                        recommended_next_review_at=self._compute_recommended_next_review_at(
                            now=now,
                            last_practice_at=None,
                            status=status,
                            mastery_score=mastery_score,
                        ),
                        updated_at=now,
                    )
                )
                continue

            # Calculate metrics for this microconcept
            total_events = len(events)
            correct_events = sum(1 for e in events if e.is_correct)
            hint_events = sum(1 for e in events if e.hint_used and e.hint_used != "none")

            accuracy = correct_events / total_events if total_events > 0 else 0.0
            hint_rate = hint_events / total_events if total_events > 0 else 0.0

            # Recency factor: more recent practice = higher score
            last_practice = events[0].timestamp_start
            days_since_practice = (now - last_practice).days
            recency_factor = max(0.5, 1.0 - (days_since_practice / 30.0))

            # Calculate mastery score
            mastery_score = accuracy * (1.0 - hint_rate) * recency_factor

            # Determine status
            if mastery_score >= 0.8:
                status = "dominant"
            elif mastery_score >= 0.5:
                status = "in_progress"
            else:
                status = "at_risk"

            mastery_states.append(
                MasteryState(
                    student_id=student_id,
                    microconcept_id=mc.id,
                    mastery_score=round(mastery_score, 4),
                    status=status,
                    last_practice_at=last_practice,
                    recommended_next_review_at=self._compute_recommended_next_review_at(
                        now=now,
                        last_practice_at=last_practice,
                        status=status,
                        mastery_score=mastery_score,
                    ),
                    updated_at=now,
                )
            )

        return mastery_states

    def recalculate_and_save_metrics(
        self,
        db: Session,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
    ) -> tuple[MetricAggregate, list[MasteryState]]:
        """
        Recalculate metrics and mastery states, and save them to the database.
        Returns the calculated metrics and mastery states.
        """
        # Calculate metrics
        metrics = self.calculate_student_metrics(db, student_id, subject_id, term_id)

        # Save or update metrics
        existing_metrics = (
            db.query(MetricAggregate)
            .filter(
                MetricAggregate.student_id == student_id,
                MetricAggregate.scope_type == "subject",
                MetricAggregate.scope_id == subject_id,
            )
            .order_by(MetricAggregate.computed_at.desc())
            .first()
        )

        if existing_metrics:
            # Update existing
            for key, value in metrics.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing_metrics, key, value)
            db.commit()
            db.refresh(existing_metrics)
            metrics = existing_metrics
        else:
            # Create new
            db.add(metrics)
            db.commit()
            db.refresh(metrics)

        # Calculate mastery states
        mastery_states = self.calculate_mastery_states(db, student_id, subject_id, term_id)

        # Save or update mastery states
        for ms in mastery_states:
            existing_ms = (
                db.query(MasteryState)
                .filter(
                    MasteryState.student_id == student_id,
                    MasteryState.microconcept_id == ms.microconcept_id,
                )
                .first()
            )

            if existing_ms:
                # Update existing
                existing_ms.mastery_score = ms.mastery_score
                existing_ms.status = ms.status
                existing_ms.last_practice_at = ms.last_practice_at
                existing_ms.recommended_next_review_at = ms.recommended_next_review_at
                existing_ms.updated_at = ms.updated_at

                # Update the object in our list so it has the ID
                ms.id = existing_ms.id
            else:
                # Create new
                db.add(ms)

        db.commit()

        return metrics, mastery_states


# Singleton instance
metric_service = MetricService()
