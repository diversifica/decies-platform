import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.activity import ActivityType
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item, ItemType
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
from app.models.recommendation import RecommendationInstance, TutorDecision
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User

client = TestClient(app)


@pytest.fixture
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter_by(name=name).first()
    if role:
        return role
    role = Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _login(email: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/login/access-token", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_e2e_04_grade_report_recommendation_outcome_flow(db_session: Session):
    """
    Covers: registrar calificación -> generar informe -> aceptar recomendación -> evaluar outcome.
    """
    uid = uuid.uuid4()
    password = "pw"

    role_tutor = _ensure_role(db_session, "Tutor")
    role_student = _ensure_role(db_session, "Student")

    tutor_user = User(
        id=uuid.uuid4(),
        email=f"t4_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"s4_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor E2E-04")

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    subject = Subject(name=f"Math E2E-04 {uid}", tutor_id=tutor_user.id)
    db_session.add_all([tutor, year, term, subject])
    db_session.flush()

    student = Student(user_id=student_user.id, subject_id=subject.id)
    db_session.add(student)
    db_session.flush()

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(id=uuid.uuid4(), code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)

    db_session.commit()

    mc = MicroConcept(
        id=uuid.uuid4(),
        subject_id=subject.id,
        term_id=term.id,
        code="MC-E2E-04",
        name="Concepto E2E-04",
        description="Microconcepto para flujo E2E-04",
        active=True,
    )
    db_session.add(mc)
    db_session.flush()

    now = datetime.utcnow()
    db_session.add(
        MetricAggregate(
            id=uuid.uuid4(),
            student_id=student.id,
            scope_type="subject",
            scope_id=subject.id,
            window_start=now - timedelta(days=30),
            window_end=now,
            accuracy=0.4,
            first_attempt_accuracy=0.4,
            error_rate=0.6,
            median_response_time_ms=10000,
            attempts_per_item_avg=1.0,
            hint_rate=0.0,
            abandon_rate=0.0,
            computed_at=now,
        )
    )
    db_session.add(
        MasteryState(
            id=uuid.uuid4(),
            student_id=student.id,
            microconcept_id=mc.id,
            mastery_score=0.2,
            status="at_risk",
            last_practice_at=None,
            recommended_next_review_at=None,
            updated_at=now,
        )
    )

    upload = ContentUpload(
        id=uuid.uuid4(),
        file_name="e2e_04.pdf",
        storage_uri="/test/e2e_04.pdf",
        mime_type="application/pdf",
        upload_type=ContentUploadType.pdf,
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        page_count=1,
    )
    db_session.add(upload)
    db_session.flush()

    item = Item(
        id=uuid.uuid4(),
        content_upload_id=upload.id,
        microconcept_id=mc.id,
        type=ItemType.MCQ,
        stem="¿Cuánto es 1+1?",
        options=["1", "2", "3"],
        correct_answer="2",
        explanation="1+1=2.",
        difficulty=1,
        is_active=True,
    )
    db_session.add(item)
    db_session.commit()

    tutor_headers = _login(tutor_user.email, password)
    student_headers = _login(student_user.email, password)

    # 1) Tutor registra una calificación.
    grade_res = client.post(
        "/api/v1/grades",
        json={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "assessment_date": date.today().isoformat(),
            "grade_value": 7.0,
            "grading_scale": "0-10",
            "notes": "E2E-04 grade",
            "scope_tags": [{"microconcept_id": str(mc.id), "weight": 1.0}],
        },
        headers=tutor_headers,
    )
    assert grade_res.status_code == 201

    # 2) Generar informe (incluye calificaciones y recomendaciones).
    report_res = client.post(
        f"/api/v1/reports/students/{student.id}/generate",
        params={
            "tutor_id": str(tutor.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "generate_recommendations": "true",
        },
        headers=tutor_headers,
    )
    assert report_res.status_code == 201
    report = report_res.json()
    assert any(s["section_type"] == "real_grades" for s in report["sections"])
    assert any(s["section_type"] == "review_schedule" for s in report["sections"])
    assert any(s["section_type"] == "recommendations" for s in report["sections"])
    assert any(s["section_type"] == "recommendation_outcomes" for s in report["sections"])

    # 3) Aceptar una recomendación (R01 o R11).
    recs_res = client.get(
        f"/api/v1/recommendations/students/{student.id}",
        params={
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "status_filter": "pending",
            "generate": "false",
        },
        headers=tutor_headers,
    )
    assert recs_res.status_code == 200
    pending_recs = recs_res.json()
    assert pending_recs
    target_rec = next((r for r in pending_recs if r["rule_id"] == "R01"), pending_recs[0])

    decision_res = client.post(
        f"/api/v1/recommendations/{target_rec['id']}/decision",
        json={
            "recommendation_id": target_rec["id"],
            "decision": "accepted",
            "tutor_id": str(tutor.id),
            "notes": "E2E-04 accept",
        },
        headers=tutor_headers,
    )
    assert decision_res.status_code == 200

    # Move decision_at to the past so outcome window can be evaluated now.
    db_session.expire_all()
    rec_id = uuid.UUID(target_rec["id"])
    rec = db_session.get(RecommendationInstance, rec_id)
    assert rec is not None
    rec.evaluation_window_days = 1

    decision = db_session.query(TutorDecision).filter_by(recommendation_id=rec_id).first()
    assert decision is not None
    decision_at = datetime.utcnow() - timedelta(days=2)
    decision.decision_at = decision_at
    db_session.add_all([rec, decision])
    db_session.commit()

    # 4) Registrar eventos en ventana pre/post para evaluar outcome.
    session_res = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(quiz_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 1,
            "content_upload_id": str(upload.id),
            "device_type": "web",
        },
        headers=student_headers,
    )
    assert session_res.status_code == 200
    session_id = session_res.json()["id"]

    items_res = client.get(
        f"/api/v1/activities/sessions/{session_id}/items", headers=student_headers
    )
    assert items_res.status_code == 200
    picked_item_id = items_res.json()[0]["id"]

    pre_ts = decision_at - timedelta(hours=12)
    post_ts = decision_at + timedelta(hours=12)

    pre_event_res = client.post(
        f"/api/v1/activities/sessions/{session_id}/responses",
        json={
            "student_id": str(student.id),
            "item_id": picked_item_id,
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "microconcept_id": None,
            "activity_type_id": str(quiz_type.id),
            "is_correct": False,
            "duration_ms": 1000,
            "attempt_number": 1,
            "response_normalized": "1",
            "hint_used": None,
            "difficulty_at_time": None,
            "timestamp_start": pre_ts.isoformat(),
            "timestamp_end": (pre_ts + timedelta(seconds=1)).isoformat(),
        },
        headers=student_headers,
    )
    assert pre_event_res.status_code == 200
    assert pre_event_res.json()["is_correct"] is False

    post_event_res = client.post(
        f"/api/v1/activities/sessions/{session_id}/responses",
        json={
            "student_id": str(student.id),
            "item_id": picked_item_id,
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "microconcept_id": None,
            "activity_type_id": str(quiz_type.id),
            "is_correct": False,
            "duration_ms": 1000,
            "attempt_number": 1,
            "response_normalized": "2",
            "hint_used": None,
            "difficulty_at_time": None,
            "timestamp_start": post_ts.isoformat(),
            "timestamp_end": (post_ts + timedelta(seconds=1)).isoformat(),
        },
        headers=student_headers,
    )
    assert post_event_res.status_code == 200
    assert post_event_res.json()["is_correct"] is True

    # 5) Evaluar outcomes.
    outcomes_res = client.post(
        "/api/v1/recommendations/outcomes/compute",
        params={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "force": "true",
        },
        headers=tutor_headers,
    )
    assert outcomes_res.status_code == 200
    outcomes_payload = outcomes_res.json()
    assert outcomes_payload["created"] >= 1
    assert outcomes_payload["pending"] == 0

    accepted_res = client.get(
        f"/api/v1/recommendations/students/{student.id}",
        params={
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "status_filter": "accepted",
            "generate": "false",
        },
        headers=tutor_headers,
    )
    assert accepted_res.status_code == 200
    accepted = accepted_res.json()
    assert any(r.get("outcome") for r in accepted)
    outcome_rec = next(r for r in accepted if r.get("outcome"))
    assert outcome_rec["outcome"]["success"] in {"true", "partial", "false"}
    assert outcome_rec["outcome"]["delta_accuracy"] is not None

    # 6) El informe debe reflejar outcomes en su sección correspondiente.
    report2_res = client.post(
        f"/api/v1/reports/students/{student.id}/generate",
        params={
            "tutor_id": str(tutor.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "generate_recommendations": "false",
        },
        headers=tutor_headers,
    )
    assert report2_res.status_code == 201
    report2 = report2_res.json()
    section = next(s for s in report2["sections"] if s["section_type"] == "recommendation_outcomes")
    assert section["data"]["stats"]["with_outcome"] >= 1
    assert any(e.get("outcome") for e in section["data"]["accepted"])
