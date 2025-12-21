import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.activity import ActivityType
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


def _ensure_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter_by(name=name).first()
    if role:
        return role
    role = Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _ensure_activity_type(db: Session, code: str) -> ActivityType:
    activity_type = db.query(ActivityType).filter_by(code=code).first()
    if activity_type:
        return activity_type
    activity_type = ActivityType(id=uuid.uuid4(), code=code, name=code, active=True)
    db.add(activity_type)
    db.commit()
    db.refresh(activity_type)
    return activity_type


def _login(email: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/login/access-token", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_e2e_06_real_grade_triggers_external_validation_recommendations_in_report(
    db_session: Session,
):
    """
    Covers: real grades -> external_validation recs -> tutor report.
    """
    uid = uuid.uuid4()
    password = "pw"

    role_tutor = _ensure_role(db_session, "Tutor")
    role_student = _ensure_role(db_session, "Student")

    tutor_user = User(
        id=uuid.uuid4(),
        email=f"t6_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"s6_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor E2E-06")

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    subject = Subject(name=f"Subject E2E-06 {uid}", tutor_id=tutor_user.id)
    db_session.add_all([tutor, year, term, subject])
    db_session.flush()

    student = Student(user_id=student_user.id, subject_id=subject.id)
    db_session.add(student)
    db_session.flush()

    _ensure_activity_type(db_session, "QUIZ")

    microconcept = MicroConcept(
        id=uuid.uuid4(),
        subject_id=subject.id,
        term_id=term.id,
        code="MC-E2E-06",
        name="Concepto E2E-06",
        description="Microconcepto para validación externa",
        active=True,
    )
    db_session.add(microconcept)
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
            accuracy=0.7,
            first_attempt_accuracy=0.7,
            error_rate=0.3,
            median_response_time_ms=8000,
            attempts_per_item_avg=1.1,
            hint_rate=0.05,
            abandon_rate=0.0,
            computed_at=now,
        )
    )
    db_session.add(
        MasteryState(
            id=uuid.uuid4(),
            student_id=student.id,
            microconcept_id=microconcept.id,
            mastery_score=0.9,
            status="dominant",
            last_practice_at=now - timedelta(days=2),
            recommended_next_review_at=now + timedelta(days=7),
            updated_at=now,
        )
    )
    db_session.commit()

    tutor_headers = _login(tutor_user.email, password)

    # 1) Registrar una calificación real baja, sin etiquetar, para disparar external_validation.
    grade_res = client.post(
        "/api/v1/grades",
        json={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "assessment_date": date.today().isoformat(),
            "grade_value": 4.0,
            "grading_scale": "0-10",
            "notes": "E2E-06 grade",
            "scope_tags": [],
        },
        headers=tutor_headers,
    )
    assert grade_res.status_code == 201

    # 2) Generar informe (incluye grades + recomendaciones).
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
    rec_section = next(s for s in report["sections"] if s["section_type"] == "recommendations")
    pending = rec_section["data"]["pending"]
    assert pending

    external = [r for r in pending if r.get("category") == "external_validation"]
    assert external
    external_codes = {r.get("rule_id") for r in external}
    assert "R33" in external_codes
    assert "R31" in external_codes

    # 3) El endpoint de recomendaciones también debe reflejar la categoría.
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
    recs = recs_res.json()
    assert recs
    assert any(r.get("category") == "external_validation" for r in recs)
