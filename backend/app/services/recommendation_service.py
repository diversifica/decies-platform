import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
from app.models.recommendation import (
    RecommendationEvidence,
    RecommendationInstance,
    RecommendationPriority,
    RecommendationStatus,
    TutorDecision,
)
from app.schemas.recommendation import (
    RecommendationEvidenceCreate,
    TutorDecisionCreate,
)


class RecommendationService:
    """Service for generating and managing study recommendations"""

    def generate_recommendations(
        self,
        db: Session,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
    ) -> list[RecommendationInstance]:
        """
        Run rules engine to generate recommendations for a student.
        Returns newly created or existing pending recommendations.
        """

        generated_recs: list[RecommendationInstance] = []

        # 1. Get Context Data
        # Latest metrics
        metrics = (
            db.query(MetricAggregate)
            .filter(
                MetricAggregate.student_id == student_id, MetricAggregate.scope_id == subject_id
            )
            .order_by(MetricAggregate.computed_at.desc())
            .first()
        )

        # Mastery states
        mastery_states = (
            db.query(MasteryState)
            .join(MicroConcept, MasteryState.microconcept_id == MicroConcept.id)
            .filter(
                MasteryState.student_id == student_id,
                MicroConcept.subject_id == subject_id,
                MicroConcept.term_id == term_id,
            )
            .all()
        )

        # 2. Rule R01: General Low Accuracy (Scope: Subject)
        # Condition: accuracy < 0.5
        if metrics and metrics.accuracy < 0.5:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                rule_id="R01",
                title="Refuerzo General Necesario",
                description=(
                    "El estudiante tiene un rendimiento global bajo "
                    f"({int(metrics.accuracy * 100)}%). Se recomienda asignar actividades "
                    "de repaso general."
                ),
                priority=RecommendationPriority.HIGH,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="accuracy",
                        value=str(metrics.accuracy),
                        description="Global Accuracy < 50%",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="error_rate",
                        value=str(metrics.error_rate),
                        description="High Error Rate",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # 3. Rule R11: Specific MicroConcept At Risk
        # Condition: status == 'at_risk' or mastery_score < 0.5
        for state in mastery_states:
            if state.status == "at_risk" or state.mastery_score < 0.5:
                # Get microconcept name
                mc = db.get(MicroConcept, state.microconcept_id)
                mc_name = mc.name if mc else "Unknown Concept"

                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    rule_id="R11",
                    title=f"Refuerzo: {mc_name}",
                    description=(
                        f"El estudiante muestra dificultades en '{mc_name}' "
                        f"(Dominio: {int(state.mastery_score * 100)}%)."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    microconcept_id=state.microconcept_id,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="mastery_state",
                            key="status",
                            value=state.status,
                            description=f"Status is {state.status}",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="mastery_state",
                            key="mastery_score",
                            value=str(state.mastery_score),
                            description="Score below threshold",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # 4. Rule R21: High Response Time (Fatigue/Doubt) (Simplified)
        # Condition: median_response_time > 30000ms (30s)
        # In a real system we'd compare vs class average or student history.
        if metrics and metrics.median_response_time_ms > 30000:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                rule_id="R21",
                title="Posible Fatiga o Duda",
                description=(
                    "El tiempo de respuesta es muy alto "
                    f"({metrics.median_response_time_ms / 1000}s). Podría indicar "
                    "distracciones, fatiga o falta de comprensión profunda."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="median_response_time_ms",
                        value=str(metrics.median_response_time_ms),
                        description="Response time > 30s",
                    )
                ],
            )
            if rec:
                generated_recs.append(rec)

        return generated_recs

    def _create_or_get_recommendation(
        self,
        db: Session,
        student_id: uuid.UUID,
        rule_id: str,
        title: str,
        description: str,
        priority: RecommendationPriority,
        evidence: list[RecommendationEvidenceCreate],
        microconcept_id: Optional[uuid.UUID] = None,
    ) -> Optional[RecommendationInstance]:
        # Check if active recommendation already exists for this rule/student/concept
        # We don't want to spam duplicates.
        existing = (
            db.query(RecommendationInstance)
            .filter(
                RecommendationInstance.student_id == student_id,
                RecommendationInstance.rule_id == rule_id,
                RecommendationInstance.status == RecommendationStatus.PENDING,
                RecommendationInstance.microconcept_id == microconcept_id,
            )
            .first()
        )

        if existing:
            return existing

        # Create new
        new_rec = RecommendationInstance(
            id=uuid.uuid4(),
            student_id=student_id,
            microconcept_id=microconcept_id,
            rule_id=rule_id,
            priority=priority,
            status=RecommendationStatus.PENDING,
            title=title,
            description=description,
            generated_at=datetime.utcnow(),
        )
        db.add(new_rec)
        db.flush()  # flush to get ID

        # Add Evidence
        for ev_data in evidence:
            ev = RecommendationEvidence(
                id=uuid.uuid4(),
                recommendation_id=new_rec.id,
                evidence_type=ev_data.evidence_type,
                key=ev_data.key,
                value=ev_data.value,
                description=ev_data.description,
            )
            db.add(ev)

        db.commit()
        db.refresh(new_rec)
        return new_rec

    def apply_tutor_decision(
        self,
        db: Session,
        decision_data: TutorDecisionCreate,
    ) -> TutorDecision:
        """
        Apply tutor decision to a recommendation.
        Updates recommendation status and creates decision log.
        """
        recommendation = db.get(RecommendationInstance, decision_data.recommendation_id)
        if not recommendation:
            raise ValueError("Recommendation not found")

        # Create Decision Log
        decision = TutorDecision(
            id=uuid.uuid4(),
            recommendation_id=decision_data.recommendation_id,
            tutor_id=decision_data.tutor_id,
            decision=decision_data.decision,
            notes=decision_data.notes,
            decision_at=datetime.utcnow(),
        )
        db.add(decision)

        # Update Recommendation Status
        if decision_data.decision == "accepted":
            recommendation.status = RecommendationStatus.ACCEPTED
        elif decision_data.decision == "rejected":
            recommendation.status = RecommendationStatus.REJECTED

        recommendation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(decision)
        return decision


recommendation_service = RecommendationService()
