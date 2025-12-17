import uuid
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.main import app
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

    tutor_user = User(
        id=uuid.uuid4(),
        email=f"t_{uid}@report.test",
        hashed_password="x",
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"s_{uid}@report.test",
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
        updated_at=datetime.utcnow(),
    )
    db_session.add_all([metrics, mastery])
    db_session.commit()

    generate_res = client.post(
        f"/api/v1/reports/students/{student.id}/generate",
        params={
            "tutor_id": str(tutor.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "generate_recommendations": "true",
        },
    )
    assert generate_res.status_code == 201
    payload = generate_res.json()
    assert payload["student_id"] == str(student.id)
    assert payload["tutor_id"] == str(tutor.id)
    assert len(payload["sections"]) >= 3

    latest_res = client.get(
        f"/api/v1/reports/students/{student.id}/latest",
        params={"tutor_id": str(tutor.id), "subject_id": str(subject.id), "term_id": str(term.id)},
    )
    assert latest_res.status_code == 200
    latest = latest_res.json()
    assert latest["id"] == payload["id"]
    assert any(s["section_type"] == "executive_summary" for s in latest["sections"])
    assert any(s["section_type"] == "recommendations" for s in latest["sections"])

