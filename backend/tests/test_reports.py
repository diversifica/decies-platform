import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.activity import ActivitySession, ActivityType
from app.models.grade import RealGrade
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
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


def test_generate_and_get_latest_report(db_session: Session):
    uid = uuid.uuid4()

    role_student = db_session.query(Role).filter_by(name="Student").first()
    if not role_student:
        role_student = Role(name="Student")
        db_session.add(role_student)

    role_tutor = db_session.query(Role).filter_by(name="Tutor").first()
    if not role_tutor:
        role_tutor = Role(name="Tutor")
        db_session.add(role_tutor)

    db_session.commit()

    password = "pw"
    tutor_user = User(
        id=uuid.uuid4(),
        email=f"t_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"s_{uid}@example.com",
        hashed_password="x",
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor Reports")
    student = Student(user_id=student_user.id)
    db_session.add_all([tutor, student])

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    db_session.add(year)
    db_session.flush()

    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    subject = Subject(name="Math Reports")
    db_session.add_all([term, subject])
    db_session.commit()

    mc = MicroConcept(subject_id=subject.id, term_id=term.id, name="Concept A", description="...")
    db_session.add(mc)
    db_session.flush()

    # Preload context so generation can pick it up
    metrics = MetricAggregate(
        student_id=student.id,
        scope_type="subject",
        scope_id=subject.id,
        window_start=datetime.utcnow(),
        window_end=datetime.utcnow(),
        accuracy=0.3,
        first_attempt_accuracy=0.2,
        error_rate=0.7,
        median_response_time_ms=35000,
        attempts_per_item_avg=1.0,
        hint_rate=0.2,
        computed_at=datetime.utcnow(),
    )
    mastery = MasteryState(
        student_id=student.id,
        microconcept_id=mc.id,
        mastery_score=0.2,
        status="at_risk",
        last_practice_at=None,
        recommended_next_review_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add_all([metrics, mastery])
    db_session.commit()

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)
        db_session.commit()

    feedback_session = ActivitySession(
        student_id=student.id,
        activity_type_id=quiz_type.id,
        subject_id=subject.id,
        term_id=term.id,
        topic_id=None,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        status="completed",
        device_type="web",
        feedback_rating=5,
        feedback_text="Me ha servido para repasar.",
        feedback_submitted_at=datetime.utcnow(),
    )
    db_session.add(feedback_session)
    db_session.commit()

    real_grade = RealGrade(
        student_id=student.id,
        subject_id=subject.id,
        term_id=term.id,
        assessment_date=date(2025, 12, 1),
        grade_value=7.5,
        grading_scale="0-10",
        notes="Buen progreso.",
        created_by_tutor_id=tutor.id,
    )
    db_session.add(real_grade)
    db_session.commit()

    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": tutor_user.email, "password": password},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    generate_res = client.post(
        f"/api/v1/reports/students/{student.id}/generate",
        params={
            "tutor_id": str(tutor.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "generate_recommendations": "true",
        },
        headers=headers,
    )
    assert generate_res.status_code == 201
    payload = generate_res.json()
    assert payload["student_id"] == str(student.id)
    assert payload["tutor_id"] == str(tutor.id)
    assert len(payload["sections"]) >= 3
    assert any(s["section_type"] == "real_grades" for s in payload["sections"])
    assert any(s["section_type"] == "review_schedule" for s in payload["sections"])

    schedule_section = next(
        s for s in payload["sections"] if s["section_type"] == "review_schedule"
    )
    assert "Vencidas" in schedule_section["content"]
    assert "Concept A" in schedule_section["content"]
    assert schedule_section["data"]["due"]

    latest_res = client.get(
        f"/api/v1/reports/students/{student.id}/latest",
        params={"tutor_id": str(tutor.id), "subject_id": str(subject.id), "term_id": str(term.id)},
        headers=headers,
    )
    assert latest_res.status_code == 200
    latest = latest_res.json()
    assert latest["id"] == payload["id"]
    assert any(s["section_type"] == "executive_summary" for s in latest["sections"])
    assert any(s["section_type"] == "review_schedule" for s in latest["sections"])
    assert any(s["section_type"] == "recommendations" for s in latest["sections"])
    assert any(s["section_type"] == "recommendation_outcomes" for s in latest["sections"])
    assert any(s["section_type"] == "student_feedback" for s in latest["sections"])

    list_res = client.get(
        "/api/v1/reports",
        params={
            "tutor_id": str(tutor.id),
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "limit": 10,
        },
        headers=headers,
    )
    assert list_res.status_code == 200
    reports = list_res.json()
    assert any(r["id"] == payload["id"] for r in reports)

    get_res = client.get(
        f"/api/v1/reports/{payload['id']}",
        params={"tutor_id": str(tutor.id)},
        headers=headers,
    )
    assert get_res.status_code == 200
    report = get_res.json()
    assert report["id"] == payload["id"]

    later_session = ActivitySession(
        student_id=student.id,
        activity_type_id=quiz_type.id,
        subject_id=subject.id,
        term_id=term.id,
        topic_id=None,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        status="completed",
        device_type="web",
        feedback_rating=4,
        feedback_text="Pude repasar bien.",
        feedback_submitted_at=datetime.utcnow() + timedelta(seconds=1),
    )
    db_session.add(later_session)
    db_session.commit()

    refreshed_res = client.get(
        f"/api/v1/reports/students/{student.id}/latest",
        params={"tutor_id": str(tutor.id), "subject_id": str(subject.id), "term_id": str(term.id)},
        headers=headers,
    )
    assert refreshed_res.status_code == 200
    refreshed = refreshed_res.json()
    assert refreshed["id"] != payload["id"]
    feedback_section = next(
        (s for s in refreshed["sections"] if s["section_type"] == "student_feedback"),
        None,
    )
    assert feedback_section is not None
    assert "No hay feedback registrado" not in feedback_section["content"]
