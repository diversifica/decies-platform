import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.microconcept import MicroConcept
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.topic import Topic
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
    if not role:
        role = Role(name=name)
        db.add(role)
        db.commit()
    return role


def _login(email: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/login/access-token", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_real_grades_crud_and_tags(db_session: Session):
    uid = uuid.uuid4()
    role_tutor = _ensure_role(db_session, "Tutor")
    role_student = _ensure_role(db_session, "Student")

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

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor Grades")
    subject = Subject(name=f"Math Grades {uid}", tutor_id=tutor_user.id)
    student = Student(user_id=student_user.id, subject_id=subject.id)
    db_session.add_all([tutor, subject, student])
    db_session.flush()

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    db_session.add(year)
    db_session.flush()
    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    db_session.add(term)
    db_session.flush()

    topic = Topic(subject_id=subject.id, term_id=term.id, name="Topic A")
    microconcept = MicroConcept(
        subject_id=subject.id, term_id=term.id, topic_id=topic.id, name="MC A"
    )
    db_session.add_all([topic, microconcept])
    db_session.commit()

    headers = _login(tutor_user.email, password)

    create_res = client.post(
        "/api/v1/grades",
        json={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "assessment_date": "2025-12-01",
            "grade_value": 7.5,
            "grading_scale": "0-10",
            "notes": "Buen progreso.",
            "scope_tags": [
                {"topic_id": str(topic.id), "microconcept_id": str(microconcept.id), "weight": 1.0}
            ],
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["student_id"] == str(student.id)
    assert created["created_by_tutor_id"] == str(tutor.id)
    assert len(created["scope_tags"]) == 1

    grade_id = created["id"]
    tag_id = created["scope_tags"][0]["id"]

    list_res = client.get(
        "/api/v1/grades",
        params={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
        },
        headers=headers,
    )
    assert list_res.status_code == 200
    assert any(g["id"] == grade_id for g in list_res.json())

    patch_res = client.patch(
        f"/api/v1/grades/{grade_id}",
        json={"grade_value": 8.25, "notes": "Mejorando."},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["grade_value"] == 8.25

    tags_res = client.get(f"/api/v1/grades/{grade_id}/tags", headers=headers)
    assert tags_res.status_code == 200
    assert len(tags_res.json()) == 1

    tag_patch = client.patch(
        f"/api/v1/grades/{grade_id}/tags/{tag_id}",
        json={"topic_id": str(topic.id), "microconcept_id": str(microconcept.id), "weight": 0.5},
        headers=headers,
    )
    assert tag_patch.status_code == 200
    assert tag_patch.json()["weight"] == 0.5

    tag_del = client.delete(f"/api/v1/grades/{grade_id}/tags/{tag_id}", headers=headers)
    assert tag_del.status_code == 204

    del_res = client.delete(f"/api/v1/grades/{grade_id}", headers=headers)
    assert del_res.status_code == 204


def test_real_grades_rbac(db_session: Session):
    uid = uuid.uuid4()
    role_tutor = _ensure_role(db_session, "Tutor")
    role_student = _ensure_role(db_session, "Student")

    password = "pw"
    tutor_user_a = User(
        id=uuid.uuid4(),
        email=f"ta_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    tutor_user_b = User(
        id=uuid.uuid4(),
        email=f"tb_{uid}@example.com",
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
    db_session.add_all([tutor_user_a, tutor_user_b, student_user])
    db_session.flush()

    tutor_a = Tutor(user_id=tutor_user_a.id, display_name="Tutor A")
    tutor_b = Tutor(user_id=tutor_user_b.id, display_name="Tutor B")
    subject = Subject(name=f"Subject {uid}", tutor_id=tutor_user_a.id)
    student = Student(user_id=student_user.id, subject_id=subject.id)
    db_session.add_all([tutor_a, tutor_b, subject, student])
    db_session.flush()

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    db_session.add_all([year, term])
    db_session.commit()

    headers_a = _login(tutor_user_a.email, password)
    headers_b = _login(tutor_user_b.email, password)

    create_res = client.post(
        "/api/v1/grades",
        json={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "assessment_date": "2025-12-01",
            "grade_value": 5.0,
        },
        headers=headers_a,
    )
    assert create_res.status_code == 201
    grade_id = create_res.json()["id"]

    forbidden = client.get(f"/api/v1/grades/{grade_id}", headers=headers_b)
    assert forbidden.status_code == 403
