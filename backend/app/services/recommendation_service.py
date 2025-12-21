import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.versioning import RECOMMENDATION_ENGINE_VERSION, RECOMMENDATION_RULESET_VERSION
from app.models.activity import ActivitySession, ActivityType, LearningEvent
from app.models.grade import RealGrade
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept, MicroConceptPrerequisite
from app.models.recommendation import (
    RecommendationEvidence,
    RecommendationInstance,
    RecommendationPriority,
    RecommendationStatus,
    TutorDecision,
)
from app.models.recommendation_catalog import RecommendationCatalog
from app.schemas.recommendation import (
    RecommendationEvidenceCreate,
    TutorDecisionCreate,
)


class RecommendationService:
    """Service for generating and managing study recommendations"""

    def __init__(self) -> None:
        self._catalog_codes_cache: set[str] | None = None

    def _get_catalog_codes(self, db: Session) -> set[str]:
        if self._catalog_codes_cache is None:
            rows = (
                db.query(RecommendationCatalog.code)
                .filter(RecommendationCatalog.active.is_(True))
                .all()
            )
            self._catalog_codes_cache = {code for (code,) in rows}
        return self._catalog_codes_cache

    @staticmethod
    def _normalize_grade(*, grade_value: float | None, grading_scale: str | None) -> float | None:
        if grade_value is None:
            return None

        value = float(grade_value)
        max_value: float | None = None

        scale = (grading_scale or "").strip()
        if "-" in scale:
            parts = [p.strip() for p in scale.split("-", 1)]
            try:
                max_value = float(parts[1])
            except ValueError:
                max_value = None

        if max_value is None:
            if value <= 10:
                max_value = 10.0
            elif value <= 100:
                max_value = 100.0

        if not max_value or max_value <= 0:
            return None

        return max(0.0, min(1.0, value / max_value))

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
        now = datetime.utcnow()

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
        accuracy = float(metrics.accuracy) if metrics and metrics.accuracy is not None else None
        first_attempt_accuracy = (
            float(metrics.first_attempt_accuracy)
            if metrics and metrics.first_attempt_accuracy is not None
            else None
        )
        hint_rate = float(metrics.hint_rate) if metrics and metrics.hint_rate is not None else None
        attempts_per_item_avg = (
            float(metrics.attempts_per_item_avg)
            if metrics and metrics.attempts_per_item_avg is not None
            else None
        )
        median_response_time_ms = (
            int(metrics.median_response_time_ms)
            if metrics and metrics.median_response_time_ms is not None
            else None
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
        mastery_by_microconcept_id = {ms.microconcept_id: ms for ms in mastery_states}

        microconcept_name_by_id: dict[uuid.UUID, str] = {}
        microconcept_ids = list(mastery_by_microconcept_id.keys())
        if microconcept_ids:
            for mc in db.query(MicroConcept).filter(MicroConcept.id.in_(microconcept_ids)).all():
                microconcept_name_by_id[mc.id] = mc.name

        # 2. Rule R01: General Low Accuracy (Scope: Subject)
        # Condition: accuracy < 0.5
        if metrics and metrics.accuracy < 0.5:
            accuracy_pct = int(
                (accuracy if accuracy is not None else float(metrics.accuracy)) * 100
            )
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R01",
                title="Refuerzo General Necesario",
                description=(
                    "El estudiante tiene un rendimiento global bajo "
                    f"({accuracy_pct}%). Se recomienda asignar actividades "
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

        # Focus rules (R02-R04, R06-R10)

        # Rule R02: Consolidate in-progress microconcepts.
        for state in mastery_states:
            if state.status != "in_progress":
                continue
            if state.last_practice_at is None:
                continue
            mastery_score = float(state.mastery_score)
            if not (0.4 <= mastery_score < 0.8):
                continue

            mc_name = microconcept_name_by_id.get(state.microconcept_id, "Microconcepto")
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R02",
                title=f"Consolidar: {mc_name}",
                description=(
                    "Aumentar práctica dirigida para consolidar microconceptos en progreso "
                    "y estabilizar el dominio."
                ),
                priority=RecommendationPriority.MEDIUM,
                microconcept_id=state.microconcept_id,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="mastery_state",
                        key="status",
                        value=state.status,
                        description="Microconcepto en progreso",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="mastery_state",
                        key="mastery_score",
                        value=str(state.mastery_score),
                        description="Dominio medio (consolidación recomendada)",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R03: Spaced review of dominant microconcepts due for review.
        due_dominant = [
            state
            for state in mastery_states
            if state.status == "dominant"
            and state.recommended_next_review_at is not None
            and state.recommended_next_review_at <= now
        ]
        if due_dominant:
            due_dominant.sort(key=lambda s: s.recommended_next_review_at or now)
            due_count = len(due_dominant)
            evidence: list[RecommendationEvidenceCreate] = [
                RecommendationEvidenceCreate(
                    evidence_type="metric_value",
                    key="due_review_count",
                    value=str(due_count),
                    description="Microconceptos dominados con repaso vencido",
                )
            ]
            for state in due_dominant[:5]:
                evidence.append(
                    RecommendationEvidenceCreate(
                        evidence_type="microconcept",
                        key="microconcept_id",
                        value=str(state.microconcept_id),
                        description=microconcept_name_by_id.get(
                            state.microconcept_id, "Microconcepto"
                        ),
                    )
                )

            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R03",
                title="Repaso espaciado de microconceptos dominados",
                description=(
                    f"Hay {due_count} microconcepto(s) dominado(s) con repaso vencido. "
                    "Recomienda una sesión de repaso espaciado (modo Revisión)."
                ),
                priority=RecommendationPriority.LOW,
                evidence=evidence,
            )
            if rec:
                generated_recs.append(rec)

        dominant_count = sum(1 for ms in mastery_states if ms.status == "dominant")
        in_progress_count = sum(1 for ms in mastery_states if ms.status == "in_progress")
        at_risk_count = sum(1 for ms in mastery_states if ms.status == "at_risk")

        # Rule R04: Reduce load of new concepts when many are at risk.
        if at_risk_count >= 3:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R04",
                title="Reducir carga de nuevos conceptos",
                description=(
                    "Hay muchos microconceptos en riesgo. Conviene reducir la introducción "
                    "de contenido nuevo y priorizar consolidación/repaso."
                ),
                priority=RecommendationPriority.MEDIUM,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="at_risk_count",
                        value=str(at_risk_count),
                        description="Número de microconceptos en riesgo",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="in_progress_count",
                        value=str(in_progress_count),
                        description="Número de microconceptos en progreso",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="dominant_count",
                        value=str(dominant_count),
                        description="Número de microconceptos dominados",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R06: Reorder the term plan if prerequisite readiness is misaligned.
        prereq_edges = (
            db.query(MicroConceptPrerequisite)
            .join(MicroConcept, MicroConceptPrerequisite.microconcept_id == MicroConcept.id)
            .filter(MicroConcept.subject_id == subject_id, MicroConcept.term_id == term_id)
            .all()
        )
        prereq_misalignment = 0
        for edge in prereq_edges:
            child = mastery_by_microconcept_id.get(edge.microconcept_id)
            prereq = mastery_by_microconcept_id.get(edge.prerequisite_microconcept_id)
            if not child or not prereq:
                continue
            if child.status in ("at_risk", "in_progress") and prereq.status != "dominant":
                prereq_misalignment += 1

        if prereq_misalignment >= 2:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R06",
                title="Reorganizar orden del trimestre",
                description=(
                    "Se detectan varios microconceptos con prerequisitos aún no dominados. "
                    "Conviene reorganizar el orden para asegurar base antes de avanzar."
                ),
                priority=RecommendationPriority.MEDIUM,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="prerequisite",
                        key="misaligned_prerequisites",
                        value=str(prereq_misalignment),
                        description="Relaciones prerequisito con dominio insuficiente",
                    )
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R07: Immediate repetition after errors for very low mastery at-risk microconcepts.
        for state in mastery_states:
            if state.status != "at_risk":
                continue
            if state.last_practice_at is None:
                continue
            if float(state.mastery_score) >= 0.3:
                continue

            mc_name = microconcept_name_by_id.get(state.microconcept_id, "Microconcepto")
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R07",
                title=f"Repetición inmediata: {mc_name}",
                description=(
                    "Se recomienda repetición inmediata tras errores para corregir el patrón "
                    "antes de seguir avanzando."
                ),
                priority=RecommendationPriority.HIGH,
                microconcept_id=state.microconcept_id,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="mastery_state",
                        key="status",
                        value=state.status,
                        description="Microconcepto en riesgo",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="mastery_state",
                        key="mastery_score",
                        value=str(state.mastery_score),
                        description="Dominio muy bajo (repetición inmediata recomendada)",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R08: Frequent micro-evaluations when activity is low and risk is present.
        week_ago = now - timedelta(days=7)
        recent_sessions = (
            db.query(ActivitySession)
            .filter(
                ActivitySession.student_id == student_id,
                ActivitySession.subject_id == subject_id,
                ActivitySession.term_id == term_id,
                ActivitySession.started_at >= week_ago,
            )
            .count()
        )
        has_risk_signal = at_risk_count > 0 or (
            metrics is not None and metrics.accuracy is not None and float(metrics.accuracy) < 0.6
        )
        if recent_sessions < 3 and has_risk_signal:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R08",
                title="Introducir microevaluaciones frecuentes",
                description=(
                    "La actividad reciente es baja y hay señales de riesgo. "
                    "Recomienda sesiones cortas y frecuentes para detectar y corregir fallos "
                    "pronto."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="recent_sessions_7d",
                        value=str(recent_sessions),
                        description="Sesiones registradas en los últimos 7 días",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="at_risk_count",
                        value=str(at_risk_count),
                        description="Número de microconceptos en riesgo",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R09: Separate confused concepts (high attempts per item suggests confusion).
        if (
            metrics is not None
            and metrics.attempts_per_item_avg is not None
            and float(metrics.attempts_per_item_avg) > 2.5
        ):
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R09",
                title="Separar conceptos confundidos",
                description=(
                    "Se observa un número alto de intentos por ítem, lo que puede indicar "
                    "confusión entre conceptos. Conviene practicar de forma más diferenciada "
                    "y con ejemplos contrastivos."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="attempts_per_item_avg",
                        value=str(metrics.attempts_per_item_avg),
                        description="Intentos por ítem elevados",
                    )
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R10: Simplify difficulty temporarily when global accuracy is very low.
        if metrics is not None and metrics.accuracy is not None and float(metrics.accuracy) < 0.4:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R10",
                title="Simplificar dificultad temporalmente",
                description=(
                    "El rendimiento global es bajo. Conviene reducir temporalmente la dificultad "
                    "para recuperar confianza y estabilizar el aprendizaje."
                ),
                priority=RecommendationPriority.MEDIUM,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="accuracy",
                        value=str(metrics.accuracy),
                        description="Precisión global baja",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="at_risk_count",
                        value=str(at_risk_count),
                        description="Microconceptos en riesgo",
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
                mc_name = microconcept_name_by_id.get(state.microconcept_id, "Unknown Concept")
                if mc_name == "Unknown Concept":
                    mc = db.get(MicroConcept, state.microconcept_id)
                    if mc:
                        mc_name = mc.name

                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
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

        # Strategy rules (R12-R20)

        # Rule R12: Limit hints if dependency is high.
        hint_rate_effective = hint_rate
        if hint_rate_effective is None:
            window_start = now - timedelta(days=30)
            total_events = (
                db.query(LearningEvent)
                .filter(
                    LearningEvent.student_id == student_id,
                    LearningEvent.subject_id == subject_id,
                    LearningEvent.term_id == term_id,
                    LearningEvent.timestamp_start >= window_start,
                )
                .count()
            )
            hint_events = (
                db.query(LearningEvent)
                .filter(
                    LearningEvent.student_id == student_id,
                    LearningEvent.subject_id == subject_id,
                    LearningEvent.term_id == term_id,
                    LearningEvent.timestamp_start >= window_start,
                    LearningEvent.hint_used.is_not(None),
                    LearningEvent.hint_used != "none",
                )
                .count()
            )
            hint_rate_effective = (hint_events / total_events) if total_events else 0.0

        if hint_rate_effective >= 0.4:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R12",
                title="Limitar uso de pistas",
                description=(
                    "Se detecta una dependencia alta de pistas. "
                    "Conviene reducir su uso gradualmente para mejorar recuperación sin ayudas."
                ),
                priority=RecommendationPriority.MEDIUM,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="hint_rate",
                        value=str(hint_rate_effective),
                        description="Tasa de uso de pistas elevada",
                    )
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R13: Replace passive review with active retrieval if first-attempt is weak.
        if first_attempt_accuracy is not None and first_attempt_accuracy < 0.5:
            if attempts_per_item_avg is None or attempts_per_item_avg >= 1.5:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R13",
                    title="Sustituir repaso pasivo por práctica activa",
                    description=(
                        "El primer intento es bajo. Recomienda priorizar práctica de recuperación "
                        "(preguntas sin apoyo) sobre repaso pasivo."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="first_attempt_accuracy",
                            value=str(first_attempt_accuracy),
                            description="Primer intento bajo",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="attempts_per_item_avg",
                            value=str(attempts_per_item_avg),
                            description="Intentos por ítem (indicador de recuperación débil)",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R14: Introduce interleaving for stable performance with multiple concepts.
        if accuracy is not None and accuracy >= 0.75 and in_progress_count >= 2:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R14",
                title="Introducir intercalado",
                description=(
                    "El rendimiento es estable y hay varios microconceptos en progreso. "
                    "Conviene mezclar práctica (intercalado) para mejorar discriminación "
                    "y transferencia."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="accuracy",
                        value=str(accuracy),
                        description="Precisión estable",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="in_progress_count",
                        value=str(in_progress_count),
                        description="Microconceptos en progreso",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R15: Fall back to blocked practice when struggling (high attempts + low accuracy).
        if accuracy is not None and accuracy < 0.6 and attempts_per_item_avg is not None:
            if attempts_per_item_avg > 2.2:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R15",
                    title="Volver a práctica bloqueada",
                    description=(
                        "Se observa dificultad y muchos intentos por ítem. "
                        "Conviene practicar por bloques (menos intercalado) para estabilizar."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="accuracy",
                            value=str(accuracy),
                            description="Precisión baja",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="attempts_per_item_avg",
                            value=str(attempts_per_item_avg),
                            description="Intentos por ítem altos",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R16: Change activity type when current pattern is inefficient.
        week_ago = now - timedelta(days=7)
        recent_by_type = (
            db.query(ActivityType.code, func.count(ActivitySession.id))
            .join(ActivityType, ActivitySession.activity_type_id == ActivityType.id)
            .filter(
                ActivitySession.student_id == student_id,
                ActivitySession.subject_id == subject_id,
                ActivitySession.term_id == term_id,
                ActivitySession.started_at >= week_ago,
            )
            .group_by(ActivityType.code)
            .all()
        )
        total_recent_sessions = sum(count for _code, count in recent_by_type)
        top_code = None
        top_count = 0
        for code, count in recent_by_type:
            if int(count) > top_count:
                top_code = code
                top_count = int(count)

        if total_recent_sessions >= 3 and top_code == "QUIZ":
            if (median_response_time_ms is not None and median_response_time_ms > 20000) or (
                accuracy is not None and accuracy < 0.65
            ):
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R16",
                    title="Cambiar tipo de actividad",
                    description=(
                        "La mayor parte de la práctica reciente es tipo Quiz "
                        "y hay señales de ineficiencia. "
                        "Conviene alternar a Match/Cloze o sesiones más cortas "
                        "para variar el formato."
                    ),
                    priority=RecommendationPriority.LOW,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="recent_sessions_7d",
                            value=str(total_recent_sessions),
                            description="Sesiones en 7 días",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="dominant_activity_type",
                            value=str(top_code),
                            description="Tipo de actividad predominante",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="median_response_time_ms",
                            value=str(median_response_time_ms),
                            description="Tiempo mediano de respuesta",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R17: Add concrete examples for weakest at-risk microconcepts (with practice).
        at_risk_practiced = [
            ms
            for ms in mastery_states
            if ms.status == "at_risk"
            and ms.last_practice_at is not None
            and float(ms.mastery_score) < 0.4
        ]
        at_risk_practiced.sort(key=lambda ms: float(ms.mastery_score))
        for state in at_risk_practiced[:2]:
            mc_name = microconcept_name_by_id.get(state.microconcept_id, "Microconcepto")
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R17",
                title=f"Aumentar ejemplos concretos: {mc_name}",
                description=(
                    "Hay errores persistentes en este microconcepto. "
                    "Conviene añadir ejemplos guiados y practicar con soluciones explicadas."
                ),
                priority=RecommendationPriority.MEDIUM,
                microconcept_id=state.microconcept_id,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="mastery_state",
                        key="status",
                        value=state.status,
                        description="Microconcepto en riesgo",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="mastery_state",
                        key="mastery_score",
                        value=str(state.mastery_score),
                        description="Dominio bajo",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R18: Controlled variability when mastery is high (avoid overfitting).
        if (
            accuracy is not None
            and accuracy >= 0.8
            and dominant_count >= 2
            and in_progress_count >= 1
        ):
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R18",
                title="Introducir variabilidad controlada",
                description=(
                    "El rendimiento es alto. Conviene introducir variabilidad controlada "
                    "para mejorar transferencia y evitar sobreajuste a un patrón de preguntas."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="accuracy",
                        value=str(accuracy),
                        description="Precisión alta",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="dominant_count",
                        value=str(dominant_count),
                        description="Microconceptos dominados",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R19: Add explanation after error when confusion is high.
        if accuracy is not None and accuracy < 0.7 and attempts_per_item_avg is not None:
            if attempts_per_item_avg > 2.0:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R19",
                    title="Añadir explicación tras error",
                    description=(
                        "Hay señales de confusión (muchos intentos por ítem). "
                        "Conviene mostrar una explicación breve tras error "
                        "cuando el mismo fallo se repite."
                    ),
                    priority=RecommendationPriority.LOW,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="attempts_per_item_avg",
                            value=str(attempts_per_item_avg),
                            description="Intentos por ítem elevados",
                        )
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R20: Reduce anticipatory explanation when performance is very good.
        if (
            accuracy is not None
            and accuracy >= 0.85
            and median_response_time_ms is not None
            and median_response_time_ms < 8000
            and hint_rate_effective is not None
            and hint_rate_effective < 0.2
        ):
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R20",
                title="Reducir explicación anticipada",
                description=(
                    "El alumno rinde muy bien y con baja dependencia de ayudas. "
                    "Conviene reducir explicación previa excesiva y priorizar ensayo/recuperación."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="accuracy",
                        value=str(accuracy),
                        description="Precisión muy alta",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="median_response_time_ms",
                        value=str(median_response_time_ms),
                        description="Tiempo de respuesta bajo",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="hint_rate",
                        value=str(hint_rate_effective),
                        description="Baja dependencia de ayudas",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # 4. Rule R05: Reinforce Prerequisites
        # Condition: target microconcept is at_risk AND has been practiced at least once
        # (last_practice_at set).
        # Action: recommend practicing up to 2 weakest prerequisites (non-dominant).
        for state in mastery_states:
            if state.status != "at_risk" or not state.last_practice_at:
                continue

            prereq_rows = (
                db.query(MicroConceptPrerequisite.prerequisite_microconcept_id)
                .join(
                    MicroConcept,
                    MicroConcept.id == MicroConceptPrerequisite.prerequisite_microconcept_id,
                )
                .filter(
                    MicroConceptPrerequisite.microconcept_id == state.microconcept_id,
                    MicroConcept.active == True,  # noqa: E712
                )
                .all()
            )
            prereq_ids = [row[0] for row in prereq_rows]
            if not prereq_ids:
                continue

            target_mc = db.get(MicroConcept, state.microconcept_id)
            target_name = target_mc.name if target_mc else "Unknown Concept"

            candidates: list[tuple[uuid.UUID, float]] = []
            for prereq_id in prereq_ids:
                prereq_state = mastery_by_microconcept_id.get(prereq_id)
                if not prereq_state:
                    continue
                if prereq_state.mastery_score >= 0.8:
                    continue
                candidates.append((prereq_id, float(prereq_state.mastery_score)))

            candidates.sort(key=lambda t: t[1])
            for prereq_id, prereq_score in candidates[:2]:
                prereq_mc = db.get(MicroConcept, prereq_id)
                prereq_name = prereq_mc.name if prereq_mc else "Unknown Prerequisite"

                prereq_state = mastery_by_microconcept_id.get(prereq_id)
                prereq_status = prereq_state.status if prereq_state else "unknown"

                priority = (
                    RecommendationPriority.HIGH
                    if float(state.mastery_score) < 0.3
                    else RecommendationPriority.MEDIUM
                )

                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R05",
                    title=f"Reforzar prerequisito: {prereq_name}",
                    description=(
                        f"El estudiante muestra dificultades en '{target_name}'. "
                        f"Se recomienda reforzar el prerequisito '{prereq_name}' "
                        "antes de continuar."
                    ),
                    priority=priority,
                    microconcept_id=prereq_id,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="prerequisite",
                            key="target_microconcept_id",
                            value=str(state.microconcept_id),
                            description=f"Target concept: {target_name}",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="prerequisite",
                            key="target_mastery_score",
                            value=str(state.mastery_score),
                            description="Target mastery is at_risk",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="prerequisite",
                            key="prerequisite_status",
                            value=str(prereq_status),
                            description="Prerequisite is not dominant",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="prerequisite",
                            key="prerequisite_mastery_score",
                            value=str(prereq_score),
                            description="Prerequisite mastery below dominant threshold",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # 5. Rule R21: High Response Time (Fatigue/Doubt) (Simplified)
        # Condition: median_response_time > 30000ms (30s)
        # In a real system we'd compare vs class average or student history.
        if metrics and metrics.median_response_time_ms > 30000:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
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

        # External validation rules (R31-R40): real grades vs system signals.
        external_validation_fired = False
        grades = (
            db.query(RealGrade)
            .options(selectinload(RealGrade.scope_tags))
            .filter(
                RealGrade.student_id == student_id,
                RealGrade.subject_id == subject_id,
                RealGrade.term_id == term_id,
            )
            .order_by(RealGrade.assessment_date.desc(), RealGrade.created_at.desc().nullslast())
            .limit(5)
            .all()
        )
        latest_grade = grades[0] if grades else None
        prev_grade = grades[1] if len(grades) > 1 else None

        latest_grade_norm = (
            self._normalize_grade(
                grade_value=float(latest_grade.grade_value) if latest_grade else None,
                grading_scale=latest_grade.grading_scale if latest_grade else None,
            )
            if latest_grade
            else None
        )

        mastery_avg_subject = (
            (sum(float(ms.mastery_score) for ms in mastery_states) / len(mastery_states))
            if mastery_states
            else None
        )

        weighted_mastery = 0.0
        weighted_total = 0.0
        tag_microconcept_ids: list[uuid.UUID] = []
        if latest_grade and latest_grade.scope_tags:
            for tag in latest_grade.scope_tags:
                if tag.microconcept_id:
                    tag_microconcept_ids.append(tag.microconcept_id)
                    ms = mastery_by_microconcept_id.get(tag.microconcept_id)
                    if not ms:
                        continue
                    weight = float(tag.weight) if tag.weight is not None else 1.0
                    weighted_mastery += float(ms.mastery_score) * weight
                    weighted_total += weight
        mastery_avg_grade_scope = (weighted_mastery / weighted_total) if weighted_total else None

        # Helper: always attach grade reference evidence when emitting external_validation recs.
        def _grade_evidence(grade: RealGrade) -> list[RecommendationEvidenceCreate]:
            return [
                RecommendationEvidenceCreate(
                    evidence_type="real_grade",
                    key="real_grade_id",
                    value=str(grade.id),
                    description="Referencia a calificación real",
                ),
                RecommendationEvidenceCreate(
                    evidence_type="real_grade",
                    key="assessment_date",
                    value=grade.assessment_date.isoformat(),
                    description="Fecha de evaluación",
                ),
                RecommendationEvidenceCreate(
                    evidence_type="real_grade",
                    key="grade_value",
                    value=str(grade.grade_value),
                    description="Valor de calificación",
                ),
                RecommendationEvidenceCreate(
                    evidence_type="real_grade",
                    key="grading_scale",
                    value=str(grade.grading_scale or ""),
                    description="Escala de calificación",
                ),
            ]

        if latest_grade and latest_grade_norm is not None:
            # R33: request tagging/context if scope is ambiguous and grade isn't excellent.
            if (
                not latest_grade.scope_tags or not tag_microconcept_ids
            ) and latest_grade_norm < 0.8:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R33",
                    title="Etiquetado por tutor",
                    description=(
                        "Hay una calificación real registrada, pero no está etiquetada por "
                        "topic/microconcepto. Etiquetar el alcance ayuda a "
                        "interpretar discrepancias y ajustar la práctica."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    evidence=_grade_evidence(latest_grade)
                    + [
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="scope_tags_count",
                            value=str(len(latest_grade.scope_tags or [])),
                            description="Número de etiquetas de alcance",
                        )
                    ],
                )
                if rec:
                    generated_recs.append(rec)
                    external_validation_fired = True

            effective_mastery = mastery_avg_grade_scope or mastery_avg_subject

            # R31: exam-style practice when grade is low but mastery seems ok.
            if (
                effective_mastery is not None
                and latest_grade_norm < 0.6
                and effective_mastery >= 0.75
            ):
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R31",
                    title="Ejercicios tipo examen",
                    description=(
                        "La calificación real es baja pese a señales de "
                        "dominio/precisión aceptables. Conviene introducir ejercicios tipo examen "
                        "para mejorar rendimiento en evaluación real."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    evidence=_grade_evidence(latest_grade)
                    + [
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="mastery_avg_scope",
                            value=str(effective_mastery),
                            description="Dominio medio en el alcance evaluado",
                        )
                    ],
                )
                if rec:
                    generated_recs.append(rec)
                    external_validation_fired = True

            # R35: prioritize key concepts (high weight tags) with low mastery.
            if latest_grade.scope_tags and tag_microconcept_ids:
                key_tags = [
                    t
                    for t in latest_grade.scope_tags
                    if (
                        t.microconcept_id
                        and (float(t.weight) if t.weight is not None else 0.0) >= 0.5
                    )
                ]
                weak_key_tags: list[tuple[float, uuid.UUID, float]] = []
                for t in key_tags:
                    ms = mastery_by_microconcept_id.get(t.microconcept_id)
                    if not ms:
                        continue
                    score = float(ms.mastery_score)
                    if score < 0.6 or ms.status != "dominant":
                        w = float(t.weight) if t.weight is not None else 1.0
                        weak_key_tags.append((score, t.microconcept_id, w))

                weak_key_tags.sort(key=lambda x: x[0])
                for score, mcid, weight in weak_key_tags[:3]:
                    mc_name = microconcept_name_by_id.get(mcid, "Microconcepto")
                    rec = self._create_or_get_recommendation(
                        db,
                        student_id=student_id,
                        subject_id=subject_id,
                        term_id=term_id,
                        rule_id="R35",
                        title=f"Priorizar conceptos clave del examen: {mc_name}",
                        description=(
                            "La calificación real indica que este microconcepto es clave "
                            "(alto peso). "
                            "El dominio actual no es suficiente. "
                            "Conviene priorizar práctica dirigida."
                        ),
                        priority=RecommendationPriority.HIGH,
                        microconcept_id=mcid,
                        evidence=_grade_evidence(latest_grade)
                        + [
                            RecommendationEvidenceCreate(
                                evidence_type="summary",
                                key="tag_weight",
                                value=str(weight),
                                description="Peso del microconcepto en la evaluación",
                            ),
                            RecommendationEvidenceCreate(
                                evidence_type="mastery_state",
                                key="mastery_score",
                                value=str(score),
                                description="Dominio actual del microconcepto",
                            ),
                        ],
                    )
                    if rec:
                        generated_recs.append(rec)
                        external_validation_fired = True

            # R36: false mastery / overconfidence if mastery is very high but grade is very low.
            if (
                effective_mastery is not None
                and latest_grade_norm <= 0.5
                and effective_mastery >= 0.85
            ):
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R36",
                    title="Reducir confianza excesiva",
                    description=(
                        "La calificación real contradice un dominio alto. "
                        "Conviene revisar supuestos y ajustar el diagnóstico "
                        "para evitar falso dominio."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    evidence=_grade_evidence(latest_grade)
                    + [
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="mastery_avg_scope",
                            value=str(effective_mastery),
                            description="Dominio medio en el alcance evaluado",
                        )
                    ],
                )
                if rec:
                    generated_recs.append(rec)
                    external_validation_fired = True

            # R32: syllabus alignment if grade is low and there's little practice data.
            events_30d = (
                db.query(LearningEvent.id)
                .filter(
                    LearningEvent.student_id == student_id,
                    LearningEvent.subject_id == subject_id,
                    LearningEvent.term_id == term_id,
                    LearningEvent.timestamp_start >= (now - timedelta(days=30)),
                )
                .count()
            )
            if latest_grade_norm < 0.6 and events_30d < 20:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R32",
                    title="Revisar alineación temario",
                    description=(
                        "La calificación real es baja y hay poca evidencia de práctica/coverage. "
                        "Conviene revisar si los ítems cubren el temario real evaluado."
                    ),
                    priority=RecommendationPriority.LOW,
                    evidence=_grade_evidence(latest_grade)
                    + [
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="events_30d",
                            value=str(events_30d),
                            description="Eventos en últimos 30 días",
                        )
                    ],
                )
                if rec:
                    generated_recs.append(rec)
                    external_validation_fired = True

            # R34: reinforce transfer when system performance is very high but grade is low.
            if latest_grade_norm < 0.6 and accuracy is not None and accuracy >= 0.8:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R34",
                    title="Reforzar transferencia",
                    description=(
                        "El desempeño en la plataforma es alto pero la calificación real es baja. "
                        "Conviene reforzar transferencia con variación de formatos y contexto."
                    ),
                    priority=RecommendationPriority.LOW,
                    evidence=_grade_evidence(latest_grade)
                    + [
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="accuracy",
                            value=str(accuracy),
                            description="Precisión global alta",
                        )
                    ],
                )
                if rec:
                    generated_recs.append(rec)
                    external_validation_fired = True

            # R37: review session consistency when per-session accuracy varies a lot.
            session_rows = (
                db.query(ActivitySession.id)
                .filter(
                    ActivitySession.student_id == student_id,
                    ActivitySession.subject_id == subject_id,
                    ActivitySession.term_id == term_id,
                    ActivitySession.started_at >= (now - timedelta(days=30)),
                )
                .order_by(ActivitySession.started_at.desc())
                .limit(10)
                .all()
            )
            session_ids = [row[0] for row in session_rows]
            per_session_acc: list[float] = []
            if session_ids:
                events = (
                    db.query(LearningEvent.session_id, LearningEvent.is_correct)
                    .filter(LearningEvent.session_id.in_(session_ids))
                    .all()
                )
                by_session: dict[uuid.UUID, list[bool]] = {}
                for sid, is_correct in events:
                    by_session.setdefault(sid, []).append(bool(is_correct))
                for sid, values in by_session.items():
                    if len(values) < 3:
                        continue
                    per_session_acc.append(sum(1 for v in values if v) / len(values))

            if len(per_session_acc) >= 5:
                mean = sum(per_session_acc) / len(per_session_acc)
                variance = sum((x - mean) ** 2 for x in per_session_acc) / len(per_session_acc)
                std = variance**0.5
                if std >= 0.25:
                    rec = self._create_or_get_recommendation(
                        db,
                        student_id=student_id,
                        subject_id=subject_id,
                        term_id=term_id,
                        rule_id="R37",
                        title="Revisar consistencia entre sesiones",
                        description=(
                            "Hay variabilidad alta entre sesiones. Conviene revisar consistencia "
                            "para evitar diagnósticos erróneos."
                        ),
                        priority=RecommendationPriority.LOW,
                        evidence=_grade_evidence(latest_grade)
                        + [
                            RecommendationEvidenceCreate(
                                evidence_type="summary",
                                key="session_accuracy_std",
                                value=f"{std:.3f}",
                                description="Desviación de accuracy por sesión (últimas sesiones)",
                            ),
                            RecommendationEvidenceCreate(
                                evidence_type="summary",
                                key="session_count",
                                value=str(len(per_session_acc)),
                                description="Sesiones consideradas",
                            ),
                        ],
                    )
                    if rec:
                        generated_recs.append(rec)
                        external_validation_fired = True

            # R38/R40 depend on repeated grades.
            if prev_grade:
                prev_norm = self._normalize_grade(
                    grade_value=float(prev_grade.grade_value),
                    grading_scale=prev_grade.grading_scale,
                )

                if prev_norm is not None and prev_norm < 0.6 and latest_grade_norm < 0.6:
                    rec = self._create_or_get_recommendation(
                        db,
                        student_id=student_id,
                        subject_id=subject_id,
                        term_id=term_id,
                        rule_id="R38",
                        title="Activar revisión tutor–alumno",
                        description=(
                            "Hay discrepancias persistentes en calificaciones reales. "
                            "Conviene una revisión conjunta tutor–alumno para alinear objetivos "
                            "y práctica."
                        ),
                        priority=RecommendationPriority.MEDIUM,
                        evidence=_grade_evidence(latest_grade)
                        + [
                            RecommendationEvidenceCreate(
                                evidence_type="real_grade",
                                key="previous_real_grade_id",
                                value=str(prev_grade.id),
                                description="Calificación real previa",
                            )
                        ],
                    )
                    if rec:
                        generated_recs.append(rec)
                        external_validation_fired = True

                if (
                    prev_norm is not None
                    and prev_norm <= 0.5
                    and latest_grade_norm <= 0.5
                    and accuracy is not None
                    and accuracy < 0.6
                    and at_risk_count >= 2
                ):
                    rec = self._create_or_get_recommendation(
                        db,
                        student_id=student_id,
                        subject_id=subject_id,
                        term_id=term_id,
                        rule_id="R40",
                        title="Reevaluar tras no mejora",
                        description=(
                            "No hay mejora en calificaciones reales y el rendimiento del sistema "
                            "sigue bajo. Conviene reevaluar la estrategia y ajustar el plan."
                        ),
                        priority=RecommendationPriority.HIGH,
                        evidence=_grade_evidence(latest_grade)
                        + [
                            RecommendationEvidenceCreate(
                                evidence_type="real_grade",
                                key="previous_real_grade_id",
                                value=str(prev_grade.id),
                                description="Calificación real previa",
                            ),
                            RecommendationEvidenceCreate(
                                evidence_type="metric_value",
                                key="accuracy",
                                value=str(accuracy),
                                description="Precisión global baja",
                            ),
                        ],
                    )
                    if rec:
                        generated_recs.append(rec)
                        external_validation_fired = True

            # R39: keep strategy when grade and system are strong.
            if (
                not external_validation_fired
                and latest_grade_norm >= 0.8
                and accuracy is not None
                and accuracy >= 0.8
                and at_risk_count == 0
            ):
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R39",
                    title="Mantener estrategia actual",
                    description=(
                        "La calificación real y el rendimiento en la plataforma son consistentes "
                        "y altos. Conviene mantener la estrategia actual."
                    ),
                    priority=RecommendationPriority.LOW,
                    evidence=_grade_evidence(latest_grade)
                    + [
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="accuracy",
                            value=str(accuracy),
                            description="Precisión global alta",
                        )
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Dosage rules (R22-R30)
        sessions_7d_start = now - timedelta(days=7)
        sessions_3d_start = now - timedelta(days=3)
        sessions_30d_start = now - timedelta(days=30)

        recent_sessions_rows = (
            db.query(ActivitySession)
            .filter(
                ActivitySession.student_id == student_id,
                ActivitySession.subject_id == subject_id,
                ActivitySession.term_id == term_id,
                ActivitySession.started_at >= sessions_7d_start,
            )
            .all()
        )
        total_sessions_7d = len(recent_sessions_rows)
        abandoned_sessions_7d = sum(1 for s in recent_sessions_rows if s.status == "abandoned")
        completed_durations_min = [
            (s.ended_at - s.started_at).total_seconds() / 60
            for s in recent_sessions_rows
            if s.ended_at is not None
        ]
        avg_duration_min = (
            (sum(completed_durations_min) / len(completed_durations_min))
            if completed_durations_min
            else None
        )

        sessions_3d = sum(1 for s in recent_sessions_rows if s.started_at >= sessions_3d_start)
        sessions_per_day: dict[str, int] = {}
        for s in recent_sessions_rows:
            key = s.started_at.date().isoformat()
            sessions_per_day[key] = sessions_per_day.get(key, 0) + 1
        days_with_sessions = len(sessions_per_day)
        max_sessions_day = max(sessions_per_day.values(), default=0)

        abandon_rate_effective = (
            float(metrics.abandon_rate) if metrics and metrics.abandon_rate is not None else None
        )
        if abandon_rate_effective is None:
            sessions_30d = (
                db.query(ActivitySession)
                .filter(
                    ActivitySession.student_id == student_id,
                    ActivitySession.subject_id == subject_id,
                    ActivitySession.term_id == term_id,
                    ActivitySession.started_at >= sessions_30d_start,
                )
                .all()
            )
            total_sessions_30d = len(sessions_30d)
            abandoned_sessions_30d = sum(1 for s in sessions_30d if s.status == "abandoned")
            abandon_rate_effective = (
                abandoned_sessions_30d / total_sessions_30d if total_sessions_30d else 0.0
            )

        # Rule R22: Increase frequency of short sessions when sessions are long.
        if avg_duration_min is not None and avg_duration_min > 12 and total_sessions_7d < 6:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R22",
                title="Aumentar sesiones cortas",
                description=(
                    "Las sesiones recientes tienden a ser largas. Conviene dividir en sesiones "
                    "más cortas y frecuentes para mantener atención y reducir fatiga."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="avg_session_duration_min_7d",
                        value=f"{avg_duration_min:.1f}",
                        description="Duración media de sesión (7 días)",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="total_sessions_7d",
                        value=str(total_sessions_7d),
                        description="Sesiones en 7 días",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R23: Introduce breaks when abandonment is high.
        if abandon_rate_effective >= 0.2 or abandoned_sessions_7d >= 2:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R23",
                title="Introducir descansos",
                description=(
                    "Se detecta abandono o interrupciones frecuentes. Conviene insertar descansos "
                    "breves o pausar la sesión cuando baje la atención."
                ),
                priority=RecommendationPriority.MEDIUM,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="abandon_rate",
                        value=str(abandon_rate_effective),
                        description="Tasa de abandono estimada",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="abandoned_sessions_7d",
                        value=str(abandoned_sessions_7d),
                        description="Sesiones abandonadas en 7 días",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R24: Adjust pace when time/accuracy mismatch suggests rushing or dragging.
        if accuracy is not None and median_response_time_ms is not None:
            if (median_response_time_ms < 6000 and accuracy < 0.7) or (
                median_response_time_ms > 25000 and accuracy > 0.8
            ):
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R24",
                    title="Ajustar ritmo",
                    description=(
                        "El ritmo actual no parece óptimo. Conviene ajustar el tempo (más pausado "
                        "si se precipita con errores, o más ágil si tarda mucho con alto acierto)."
                    ),
                    priority=RecommendationPriority.LOW,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="median_response_time_ms",
                            value=str(median_response_time_ms),
                            description="Tiempo mediano de respuesta",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="accuracy",
                            value=str(accuracy),
                            description="Precisión global",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R25: Reflective pause when answering too fast with many errors.
        if accuracy is not None and median_response_time_ms is not None:
            if median_response_time_ms < 4500 and accuracy < 0.6:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R25",
                    title="Añadir pausa reflexiva",
                    description=(
                        "Se detecta respuesta muy rápida con muchos errores. Conviene añadir una "
                        "pausa breve antes de responder para mejorar precisión."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="median_response_time_ms",
                            value=str(median_response_time_ms),
                            description="Tiempo mediano muy bajo",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="accuracy",
                            value=str(accuracy),
                            description="Precisión baja",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R26: Increase automation when accuracy is high but responses are slow.
        if accuracy is not None and median_response_time_ms is not None:
            if accuracy >= 0.8 and median_response_time_ms > 15000:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R26",
                    title="Aumentar automatización",
                    description=(
                        "El alumno acierta pero tarda demasiado. Conviene practicar "
                        "para automatizar y reducir el tiempo de respuesta manteniendo el acierto."
                    ),
                    priority=RecommendationPriority.LOW,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="accuracy",
                            value=str(accuracy),
                            description="Precisión alta",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="median_response_time_ms",
                            value=str(median_response_time_ms),
                            description="Tiempo mediano alto",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R27: Reduce daily volume when activity is very high but performance is weak.
        if accuracy is not None and accuracy < 0.65:
            if total_sessions_7d >= 10 or sessions_3d >= 6:
                rec = self._create_or_get_recommendation(
                    db,
                    student_id=student_id,
                    subject_id=subject_id,
                    term_id=term_id,
                    rule_id="R27",
                    title="Reducir volumen diario",
                    description=(
                        "Hay mucha carga de práctica reciente y el rendimiento es bajo. "
                        "Conviene reducir volumen diario para evitar retroceso por sobrecarga."
                    ),
                    priority=RecommendationPriority.MEDIUM,
                    evidence=[
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="total_sessions_7d",
                            value=str(total_sessions_7d),
                            description="Sesiones en 7 días",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="summary",
                            key="sessions_3d",
                            value=str(sessions_3d),
                            description="Sesiones en 3 días",
                        ),
                        RecommendationEvidenceCreate(
                            evidence_type="metric_value",
                            key="accuracy",
                            value=str(accuracy),
                            description="Precisión baja con alta carga",
                        ),
                    ],
                )
                if rec:
                    generated_recs.append(rec)

        # Rule R28: Increase volume when performance is stable and risk is low.
        if (
            accuracy is not None
            and accuracy >= 0.85
            and at_risk_count == 0
            and total_sessions_7d < 3
        ):
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R28",
                title="Incrementar volumen",
                description=(
                    "El rendimiento es alto y estable. Conviene aumentar gradualmente el volumen "
                    "de práctica para aprovechar el margen de progreso."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="accuracy",
                        value=str(accuracy),
                        description="Precisión alta",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="total_sessions_7d",
                        value=str(total_sessions_7d),
                        description="Sesiones en 7 días",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R29: Adjust difficulty upward when performance is very strong.
        if (
            accuracy is not None
            and accuracy >= 0.9
            and median_response_time_ms is not None
            and median_response_time_ms < 8000
            and attempts_per_item_avg is not None
            and attempts_per_item_avg <= 1.3
        ):
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R29",
                title="Ajustar dificultad",
                description=(
                    "El rendimiento es muy alto y estable. Conviene aumentar la dificultad "
                    "para mantener el reto y seguir progresando."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="accuracy",
                        value=str(accuracy),
                        description="Precisión muy alta",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="median_response_time_ms",
                        value=str(median_response_time_ms),
                        description="Tiempo mediano bajo",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="metric_value",
                        key="attempts_per_item_avg",
                        value=str(attempts_per_item_avg),
                        description="Pocos intentos por ítem",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        # Rule R30: Alternate intensive and light days when practicing almost every day.
        if total_sessions_7d >= 8 and days_with_sessions >= 6:
            rec = self._create_or_get_recommendation(
                db,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                rule_id="R30",
                title="Alternar días intensivos y ligeros",
                description=(
                    "La práctica se concentra casi todos los días. Conviene alternar "
                    "días intensivos y días ligeros para estabilizar el rendimiento semanal."
                ),
                priority=RecommendationPriority.LOW,
                evidence=[
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="total_sessions_7d",
                        value=str(total_sessions_7d),
                        description="Sesiones en 7 días",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="days_with_sessions_7d",
                        value=str(days_with_sessions),
                        description="Días con sesiones en 7 días",
                    ),
                    RecommendationEvidenceCreate(
                        evidence_type="summary",
                        key="max_sessions_in_day_7d",
                        value=str(max_sessions_day),
                        description="Máximo de sesiones en un día (7 días)",
                    ),
                ],
            )
            if rec:
                generated_recs.append(rec)

        return generated_recs

    def _create_or_get_recommendation(
        self,
        db: Session,
        *,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
        rule_id: str,
        title: str,
        description: str,
        priority: RecommendationPriority,
        evidence: list[RecommendationEvidenceCreate],
        microconcept_id: Optional[uuid.UUID] = None,
        topic_id: Optional[uuid.UUID] = None,
    ) -> Optional[RecommendationInstance]:
        if rule_id not in self._get_catalog_codes(db):
            raise ValueError(
                f"Recommendation rule_id '{rule_id}' not found in recommendation_catalog"
            )

        # Check if active recommendation already exists for this rule/student/concept
        # We don't want to spam duplicates.
        existing = (
            db.query(RecommendationInstance)
            .filter(
                RecommendationInstance.student_id == student_id,
                RecommendationInstance.subject_id == subject_id,
                RecommendationInstance.term_id == term_id,
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
            subject_id=subject_id,
            term_id=term_id,
            topic_id=topic_id,
            microconcept_id=microconcept_id,
            rule_id=rule_id,
            recommendation_code=rule_id,
            priority=priority,
            status=RecommendationStatus.PENDING,
            title=title,
            description=description,
            engine_version=RECOMMENDATION_ENGINE_VERSION,
            ruleset_version=RECOMMENDATION_RULESET_VERSION,
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
