import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
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


def test_catalog_topics_tutor_scoping(db_session: Session):
    uid = uuid.uuid4()
    role_tutor = _ensure_role(db_session, "Tutor")

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
    db_session.add_all([tutor_user_a, tutor_user_b])
    db_session.flush()

    tutor_a = Tutor(user_id=tutor_user_a.id, display_name="Tutor A")
    tutor_b = Tutor(user_id=tutor_user_b.id, display_name="Tutor B")
    subject_a = Subject(name=f"Sub A {uid}", tutor_id=tutor_user_a.id)
    subject_b = Subject(name=f"Sub B {uid}", tutor_id=tutor_user_b.id)
    db_session.add_all([tutor_a, tutor_b, subject_a, subject_b])
    db_session.flush()

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    db_session.add_all([year, term])
    db_session.flush()

    topic_a = Topic(subject_id=subject_a.id, term_id=term.id, name="Topic A", order_index=1)
    topic_b = Topic(subject_id=subject_b.id, term_id=term.id, name="Topic B", order_index=1)
    db_session.add_all([topic_a, topic_b])
    db_session.commit()

    headers_a = _login(tutor_user_a.email, password)

    ok = client.get(
        "/api/v1/catalog/topics",
        params={"mine": True, "subject_id": str(subject_a.id), "term_id": str(term.id)},
        headers=headers_a,
    )
    assert ok.status_code == 200
    assert any(t["id"] == str(topic_a.id) for t in ok.json())
    assert all(t["subject_id"] == str(subject_a.id) for t in ok.json())

    forbidden = client.get(
        "/api/v1/catalog/topics",
        params={"mine": True, "subject_id": str(subject_b.id)},
        headers=headers_a,
    )
    assert forbidden.status_code == 403


def test_catalog_topics_student_scoping(db_session: Session):
    uid = uuid.uuid4()
    role_student = _ensure_role(db_session, "Student")
    role_tutor = _ensure_role(db_session, "Tutor")

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
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor")
    subject = Subject(name=f"Sub {uid}", tutor_id=tutor_user.id)
    db_session.add_all([tutor, subject])
    db_session.flush()
    student = Student(user_id=student_user.id, subject_id=subject.id)
    db_session.add(student)
    db_session.flush()

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    db_session.add_all([year, term])
    db_session.flush()

    topic = Topic(subject_id=subject.id, term_id=term.id, name="Topic A", order_index=1)
    other_subject = Subject(name=f"Sub other {uid}", tutor_id=tutor_user.id)
    db_session.add(other_subject)
    db_session.flush()
    other_topic = Topic(subject_id=other_subject.id, term_id=term.id, name="Topic B", order_index=1)
    db_session.add_all([topic, other_topic])
    db_session.commit()

    headers = _login(student_user.email, password)
    res = client.get("/api/v1/catalog/topics", headers=headers)
    assert res.status_code == 200
    topics = res.json()
    assert any(t["id"] == str(topic.id) for t in topics)
    assert all(t["subject_id"] == str(subject.id) for t in topics)
