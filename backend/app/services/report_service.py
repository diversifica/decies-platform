import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.activity import ActivitySession, ActivityType
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
from app.models.recommendation import RecommendationInstance, RecommendationStatus
from app.models.report import TutorReport, TutorReportSection
from app.services.metric_service import metric_service
from app.services.recommendation_service import recommendation_service


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _priority_to_str(value: Any) -> str:
    if value is None:
        return ""
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value
    if isinstance(value, str):
        return value
    return str(value)


def _format_feedback_entry(entry: dict[str, Any]) -> str:
    submitted_at = entry.get("submitted_at") or ""
    activity_code = entry.get("activity_type") or ""
    rating = entry.get("rating")
    text = (entry.get("text") or "").strip()

    rating_label = f"{rating}/5" if isinstance(rating, int) else "N/A"
    if text:
        return f"- [{activity_code}] {submitted_at} — {rating_label} — {text}"
    return f"- [{activity_code}] {submitted_at} — {rating_label}"


class ReportService:
    def generate_student_report(
        self,
        db: Session,
        *,
        tutor_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
        generate_recommendations: bool = True,
    ) -> TutorReport:
        metrics = (
            db.query(MetricAggregate)
            .filter(
                MetricAggregate.student_id == student_id,
                MetricAggregate.scope_type == "subject",
                MetricAggregate.scope_id == subject_id,
            )
            .order_by(MetricAggregate.computed_at.desc())
            .first()
        )

        if not metrics:
            metrics = metric_service.calculate_student_metrics(db, student_id, subject_id, term_id)
            db.add(metrics)
            db.commit()
            db.refresh(metrics)

        mastery_states = (
            db.query(MasteryState, MicroConcept)
            .join(MicroConcept, MasteryState.microconcept_id == MicroConcept.id)
            .filter(
                MasteryState.student_id == student_id,
                MicroConcept.subject_id == subject_id,
                MicroConcept.term_id == term_id,
            )
            .all()
        )
        if not mastery_states:
            calculated = metric_service.calculate_mastery_states(
                db, student_id, subject_id, term_id
            )
            for ms in calculated:
                db.add(ms)
            db.commit()

            mastery_states = (
                db.query(MasteryState, MicroConcept)
                .join(MicroConcept, MasteryState.microconcept_id == MicroConcept.id)
                .filter(
                    MasteryState.student_id == student_id,
                    MicroConcept.subject_id == subject_id,
                    MicroConcept.term_id == term_id,
                )
                .all()
            )

        if generate_recommendations:
            recommendation_service.generate_recommendations(db, student_id, subject_id, term_id)

        pending_recommendations = (
            db.query(RecommendationInstance)
            .filter(
                RecommendationInstance.student_id == student_id,
                RecommendationInstance.status == RecommendationStatus.PENDING,
            )
            .order_by(RecommendationInstance.priority, RecommendationInstance.generated_at.desc())
            .all()
        )

        feedback_sessions = (
            db.query(ActivitySession, ActivityType)
            .join(ActivityType, ActivitySession.activity_type_id == ActivityType.id)
            .filter(
                ActivitySession.student_id == student_id,
                ActivitySession.subject_id == subject_id,
                ActivitySession.term_id == term_id,
                ActivitySession.feedback_submitted_at.is_not(None),
            )
            .order_by(ActivitySession.feedback_submitted_at.desc())
            .limit(5)
            .all()
        )
        feedback_entries: list[dict[str, Any]] = []
        for session, activity_type in feedback_sessions:
            feedback_entries.append(
                {
                    "session_id": str(session.id),
                    "activity_type": activity_type.code,
                    "rating": session.feedback_rating,
                    "text": session.feedback_text,
                    "submitted_at": (
                        session.feedback_submitted_at.isoformat()
                        if session.feedback_submitted_at
                        else None
                    ),
                }
            )

        at_risk = []
        for ms, mc in mastery_states:
            if ms.status != "at_risk":
                continue
            at_risk.append(
                {
                    "microconcept_id": str(ms.microconcept_id),
                    "name": mc.name,
                    "mastery_score": _to_float(ms.mastery_score),
                }
            )
        dominant_count = sum(1 for (ms, _mc) in mastery_states if ms.status == "dominant")
        in_progress_count = sum(1 for (ms, _mc) in mastery_states if ms.status == "in_progress")
        at_risk_count = sum(1 for (ms, _mc) in mastery_states if ms.status == "at_risk")

        accuracy = _to_float(metrics.accuracy)
        first_attempt_accuracy = _to_float(metrics.first_attempt_accuracy)
        median_time_ms = metrics.median_response_time_ms

        accuracy_label = f"{accuracy * 100:.1f}%" if accuracy is not None else "N/A"
        first_attempt_label = (
            f"{first_attempt_accuracy * 100:.1f}%" if first_attempt_accuracy is not None else "N/A"
        )
        median_time_label = f"{median_time_ms / 1000:.1f}s" if median_time_ms is not None else "N/A"

        executive_lines = [
            "Resumen ejecutivo (últimos 30 días aprox.):",
            f"- Precisión global: {accuracy_label}",
            f"- Primer intento: {first_attempt_label}",
            f"- Tiempo mediano: {median_time_label}",
            (
                f"- Dominio: {dominant_count} dominados, "
                f"{in_progress_count} en progreso, "
                f"{at_risk_count} en riesgo"
            ),
            f"- Recomendaciones pendientes: {len(pending_recommendations)}",
        ]
        if at_risk_count:
            top_at_risk = ", ".join([mc["name"] for mc in at_risk[:5]])
            executive_lines.append(f"- En riesgo (top): {top_at_risk}")
        if feedback_entries:
            executive_lines.append(f"- Feedback reciente: {len(feedback_entries)} comentario(s)")

        metrics_snapshot: dict[str, Any] = {
            "accuracy": accuracy,
            "first_attempt_accuracy": first_attempt_accuracy,
            "median_response_time_ms": median_time_ms,
            "hint_rate": _to_float(metrics.hint_rate),
            "window_start": metrics.window_start.isoformat() if metrics.window_start else None,
            "window_end": metrics.window_end.isoformat() if metrics.window_end else None,
            "computed_at": metrics.computed_at.isoformat() if metrics.computed_at else None,
            "mastery_counts": {
                "dominant": dominant_count,
                "in_progress": in_progress_count,
                "at_risk": at_risk_count,
            },
            "pending_recommendations": len(pending_recommendations),
            "feedback_count": len(feedback_entries),
        }

        report = TutorReport(
            id=uuid.uuid4(),
            tutor_id=tutor_id,
            student_id=student_id,
            subject_id=subject_id,
            term_id=term_id,
            summary="\n".join(executive_lines),
            metrics_snapshot=metrics_snapshot,
            window_start=metrics.window_start,
            window_end=metrics.window_end,
        )
        db.add(report)
        db.flush()

        sections: list[TutorReportSection] = [
            TutorReportSection(
                id=uuid.uuid4(),
                report_id=report.id,
                order_index=0,
                section_type="executive_summary",
                title="Resumen ejecutivo",
                content="\n".join(executive_lines),
                data={"metrics": metrics_snapshot},
            ),
            TutorReportSection(
                id=uuid.uuid4(),
                report_id=report.id,
                order_index=1,
                section_type="mastery",
                title="Estado de dominio",
                content=(
                    f"Dominados: {dominant_count}\n"
                    f"En progreso: {in_progress_count}\n"
                    f"En riesgo: {at_risk_count}\n"
                ),
                data={"at_risk": at_risk},
            ),
            TutorReportSection(
                id=uuid.uuid4(),
                report_id=report.id,
                order_index=2,
                section_type="recommendations",
                title="Recomendaciones activas",
                content="\n".join(
                    [
                        f"- [{_priority_to_str(rec.priority)}] {rec.title}: {rec.description}"
                        for rec in pending_recommendations[:10]
                    ]
                )
                or "No hay recomendaciones pendientes.",
                data={
                    "pending": [
                        {
                            "id": str(rec.id),
                            "rule_id": rec.rule_id,
                            "priority": _priority_to_str(rec.priority),
                            "title": rec.title,
                            "description": rec.description,
                            "generated_at": rec.generated_at.isoformat(),
                        }
                        for rec in pending_recommendations
                    ]
                },
            ),
            TutorReportSection(
                id=uuid.uuid4(),
                report_id=report.id,
                order_index=3,
                section_type="student_feedback",
                title="Feedback del alumno",
                content=(
                    "\n".join([_format_feedback_entry(e) for e in feedback_entries])
                    if feedback_entries
                    else "No hay feedback registrado aún."
                ),
                data={"entries": feedback_entries},
            ),
        ]
        for section in sections:
            db.add(section)

        db.commit()
        db.refresh(report)
        return report

    def get_latest_report(
        self,
        db: Session,
        *,
        tutor_id: uuid.UUID,
        student_id: uuid.UUID,
        subject_id: uuid.UUID,
        term_id: uuid.UUID,
    ) -> TutorReport | None:
        return (
            db.query(TutorReport)
            .filter(
                TutorReport.tutor_id == tutor_id,
                TutorReport.student_id == student_id,
                TutorReport.subject_id == subject_id,
                TutorReport.term_id == term_id,
            )
            .order_by(TutorReport.generated_at.desc())
            .first()
        )


report_service = ReportService()
