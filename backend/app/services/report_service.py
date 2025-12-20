import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, selectinload

from app.models.activity import ActivitySession, ActivityType
from app.models.grade import RealGrade
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
from app.models.recommendation import RecommendationInstance, RecommendationStatus
from app.models.report import TutorReport, TutorReportSection
from app.models.topic import Topic
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


def _format_grade_entry(entry: dict[str, Any]) -> str:
    assessment_date = entry.get("assessment_date") or ""
    grade_value = entry.get("grade_value")
    grading_scale = entry.get("grading_scale")
    notes = (entry.get("notes") or "").strip()
    tags: list[str] = entry.get("tags") or []

    value_label = f"{grade_value}" if grade_value is not None else "N/A"
    scale_label = f" ({grading_scale})" if grading_scale else ""
    tags_label = f" Tags: {', '.join(tags)}" if tags else ""
    notes_label = f" — {notes}" if notes else ""
    return f"- {assessment_date}: {value_label}{scale_label}{notes_label}{tags_label}"


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

        accepted_recommendations = (
            db.query(RecommendationInstance)
            .outerjoin(MicroConcept, RecommendationInstance.microconcept_id == MicroConcept.id)
            .options(selectinload(RecommendationInstance.outcome))
            .filter(
                RecommendationInstance.student_id == student_id,
                RecommendationInstance.status == RecommendationStatus.ACCEPTED,
                or_(
                    RecommendationInstance.microconcept_id.is_(None),
                    and_(MicroConcept.subject_id == subject_id, MicroConcept.term_id == term_id),
                ),
            )
            .order_by(RecommendationInstance.updated_at.desc())
            .limit(20)
            .all()
        )

        accepted_payload: list[dict[str, Any]] = []
        with_outcome = 0
        success_true = 0
        success_false = 0
        success_partial = 0

        for rec in accepted_recommendations:
            outcome_payload = None
            if rec.outcome:
                with_outcome += 1
                normalized = (rec.outcome.success or "").lower()
                if normalized == "true":
                    success_true += 1
                elif normalized == "false":
                    success_false += 1
                else:
                    success_partial += 1

                outcome_payload = {
                    "id": str(rec.outcome.id),
                    "recommendation_id": str(rec.outcome.recommendation_id),
                    "evaluation_start": rec.outcome.evaluation_start.isoformat(),
                    "evaluation_end": rec.outcome.evaluation_end.isoformat(),
                    "success": rec.outcome.success,
                    "delta_mastery": _to_float(rec.outcome.delta_mastery),
                    "delta_accuracy": _to_float(rec.outcome.delta_accuracy),
                    "delta_hint_rate": _to_float(rec.outcome.delta_hint_rate),
                    "computed_at": rec.outcome.computed_at.isoformat(),
                    "notes": rec.outcome.notes,
                }

            accepted_payload.append(
                {
                    "id": str(rec.id),
                    "title": rec.title,
                    "description": rec.description,
                    "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
                    "outcome": outcome_payload,
                }
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

        real_grades = (
            db.query(RealGrade)
            .options(selectinload(RealGrade.scope_tags))
            .filter(
                RealGrade.student_id == student_id,
                RealGrade.subject_id == subject_id,
                RealGrade.term_id == term_id,
                RealGrade.created_by_tutor_id == tutor_id,
            )
            .order_by(RealGrade.assessment_date.desc())
            .limit(5)
            .all()
        )

        topic_ids: set[uuid.UUID] = set()
        microconcept_ids: set[uuid.UUID] = set()
        for grade in real_grades:
            for tag in grade.scope_tags:
                if tag.topic_id:
                    topic_ids.add(tag.topic_id)
                if tag.microconcept_id:
                    microconcept_ids.add(tag.microconcept_id)

        topic_by_id: dict[uuid.UUID, str] = {}
        if topic_ids:
            for topic in db.query(Topic).filter(Topic.id.in_(topic_ids)).all():
                topic_by_id[topic.id] = topic.name

        microconcept_by_id: dict[uuid.UUID, str] = {}
        if microconcept_ids:
            for mc in db.query(MicroConcept).filter(MicroConcept.id.in_(microconcept_ids)).all():
                microconcept_by_id[mc.id] = mc.name

        grade_entries: list[dict[str, Any]] = []
        grade_values: list[float] = []
        for grade in real_grades:
            numeric_grade = _to_float(grade.grade_value)
            if numeric_grade is not None:
                grade_values.append(numeric_grade)

            tags: list[str] = []
            for tag in grade.scope_tags:
                parts: list[str] = []
                if tag.topic_id:
                    parts.append(f"Topic: {topic_by_id.get(tag.topic_id, str(tag.topic_id))}")
                if tag.microconcept_id:
                    parts.append(
                        "Microconcepto: "
                        f"{microconcept_by_id.get(tag.microconcept_id, str(tag.microconcept_id))}"
                    )
                weight = _to_float(tag.weight)
                if weight is not None:
                    parts.append(f"peso={weight:g}")
                if parts:
                    tags.append(" / ".join(parts))

            grade_entries.append(
                {
                    "id": str(grade.id),
                    "assessment_date": grade.assessment_date.isoformat(),
                    "grade_value": numeric_grade,
                    "grading_scale": grade.grading_scale,
                    "notes": grade.notes,
                    "tags": tags,
                }
            )

        avg_label = "N/A"
        if grade_values:
            avg_label = f"{(sum(grade_values) / len(grade_values)):.2f}"

        trend_label = "N/A"
        if len(grade_values) >= 2:
            delta = grade_values[0] - grade_values[1]
            if abs(delta) < 1e-6:
                trend_label = "estable"
            elif delta > 0:
                trend_label = f"mejora (+{delta:.2f})"
            else:
                trend_label = f"baja ({delta:.2f})"

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

        report_now = datetime.utcnow()
        review_due: list[dict[str, Any]] = []
        review_upcoming: list[dict[str, Any]] = []
        review_unscheduled_count = 0
        for ms, mc in mastery_states:
            next_review = ms.recommended_next_review_at
            if not next_review:
                review_unscheduled_count += 1
                continue

            payload = {
                "microconcept_id": str(ms.microconcept_id),
                "name": mc.name,
                "recommended_next_review_at": next_review.isoformat(),
                "status": ms.status,
                "mastery_score": _to_float(ms.mastery_score),
            }
            if next_review <= report_now:
                review_due.append(payload)
            elif next_review <= report_now + timedelta(days=7):
                review_upcoming.append(payload)

        review_due.sort(key=lambda e: e["recommended_next_review_at"])
        review_upcoming.sort(key=lambda e: e["recommended_next_review_at"])

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
            (f"- Revisiones: {len(review_due)} vencidas, {len(review_upcoming)} próximas (7 días)"),
            f"- Recomendaciones pendientes: {len(pending_recommendations)}",
        ]
        if at_risk_count:
            top_at_risk = ", ".join([mc["name"] for mc in at_risk[:5]])
            executive_lines.append(f"- En riesgo (top): {top_at_risk}")
        if feedback_entries:
            executive_lines.append(f"- Feedback reciente: {len(feedback_entries)} comentario(s)")
        if grade_entries:
            executive_lines.append(f"- Calificaciones recientes: {len(grade_entries)}")

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
            "real_grades_count": len(grade_entries),
            "review_schedule": {
                "due": len(review_due),
                "upcoming": len(review_upcoming),
                "unscheduled": review_unscheduled_count,
            },
        }

        review_lines: list[str] = []
        if review_due:
            review_lines.append("Vencidas:")
            review_lines.extend(
                [
                    f"- {entry['name']} — {entry['recommended_next_review_at'][:10]}"
                    for entry in review_due[:10]
                ]
            )
        if review_upcoming:
            if review_lines:
                review_lines.append("")
            review_lines.append("Próximos 7 días:")
            review_lines.extend(
                [
                    f"- {entry['name']} — {entry['recommended_next_review_at'][:10]}"
                    for entry in review_upcoming[:10]
                ]
            )
        if not review_lines:
            review_lines = ["No hay revisiones vencidas o próximas."]

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
                section_type="review_schedule",
                title="Próximas revisiones",
                content="\n".join(review_lines),
                data={
                    "due": review_due,
                    "upcoming": review_upcoming,
                    "unscheduled": review_unscheduled_count,
                },
            ),
            TutorReportSection(
                id=uuid.uuid4(),
                report_id=report.id,
                order_index=3,
                section_type="real_grades",
                title="Calificaciones",
                content=(
                    "\n".join([_format_grade_entry(entry) for entry in grade_entries])
                    if grade_entries
                    else "No hay calificaciones registradas aún."
                ),
                data={
                    "recent": grade_entries,
                    "stats": {"trend": trend_label, "average_recent": avg_label},
                },
            ),
            TutorReportSection(
                id=uuid.uuid4(),
                report_id=report.id,
                order_index=4,
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
                order_index=5,
                section_type="recommendation_outcomes",
                title="Impacto de recomendaciones",
                content=(
                    "No hay recomendaciones aceptadas aún."
                    if not accepted_payload
                    else (
                        "Hay recomendaciones aceptadas, pero aún no hay impacto calculado. "
                        "En la pestaña de Recomendaciones, pulsa “Actualizar impacto”."
                        if with_outcome == 0
                        else "Impacto estimado (Δ) en métricas dentro de la ventana de evaluación."
                    )
                ),
                data={
                    "accepted": accepted_payload,
                    "stats": {
                        "total_accepted": len(accepted_payload),
                        "with_outcome": with_outcome,
                        "success_true": success_true,
                        "success_false": success_false,
                        "success_partial": success_partial,
                    },
                },
            ),
            TutorReportSection(
                id=uuid.uuid4(),
                report_id=report.id,
                order_index=6,
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
