import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.main import app
from app.models.microconcept import MicroConcept
from app.models.role import Role
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User

client = TestClient(app)


@pytest.fixture
def db_session() -> Session:
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_or_create_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter(func.lower(Role.name) == name.casefold()).first()
    if role:
        return role
    role = Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _login(email: str, password: str) -> dict[str, str]:
    token_res = client.post(
        "/api/v1/login/access-token", json={"email": email, "password": password}
    )
    assert token_res.status_code == 200
    return {"Authorization": f"Bearer {token_res.json()['access_token']}"}


def _create_tutor_scope(db: Session) -> tuple[User, Tutor, Subject, Term, dict[str, str]]:
    role = _get_or_create_role(db, "tutor")
    password = "pw"
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"tutor_mc_{user_id}@test.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role.id,
    )
    db.add(user)
    db.flush()

    tutor = Tutor(user_id=user.id, display_name="Test Tutor")
    db.add(tutor)
    db.flush()

    ac_year = AcademicYear(
        name=f"2025-2026-mc-{user_id}",
        start_date="2025-09-01",
        end_date="2026-06-30",
    )
    db.add(ac_year)
    db.flush()

    term = Term(academic_year_id=ac_year.id, code="T1", name="Term 1")
    subject = Subject(name=f"Subject MC {user_id}", tutor_id=user.id)
    db.add_all([term, subject])
    db.commit()

    headers = _login(user.email, password)
    return user, tutor, subject, term, headers


def test_microconcepts_tutor_can_create_list_and_update(db_session: Session):
    _user, _tutor, subject, term, headers = _create_tutor_scope(db_session)

    create_res = client.post(
        "/api/v1/microconcepts",
        json={
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "code": "MC-T-001",
            "name": "Números enteros",
            "description": "Concepto base",
            "active": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    mc_id = create_res.json()["id"]

    list_res = client.get(
        f"/api/v1/microconcepts/subjects/{subject.id}",
        params={"term_id": str(term.id)},
        headers=headers,
    )
    assert list_res.status_code == 200
    assert any(row["id"] == mc_id for row in list_res.json())

    patch_res = client.patch(
        f"/api/v1/microconcepts/{mc_id}",
        json={"name": "Números enteros (editado)", "active": False},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Números enteros (editado)"
    assert patch_res.json()["active"] is False

    mc = db_session.query(MicroConcept).filter_by(id=uuid.UUID(mc_id)).first()
    assert mc is not None
    assert mc.active is False


def test_microconcepts_student_forbidden(db_session: Session):
    role_student = _get_or_create_role(db_session, "student")
    password = "pw"
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"student_mc_{user_id}@test.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add(user)
    db_session.commit()
    headers = _login(user.email, password)

    res = client.get(f"/api/v1/microconcepts/subjects/{uuid.uuid4()}", headers=headers)
    assert res.status_code == 403


def test_microconcepts_tutor_cannot_access_other_tutor_subject(db_session: Session):
    _user_a, _tutor_a, _subject_a, _term_a, headers_a = _create_tutor_scope(db_session)
    _user_b, _tutor_b, subject_b, term_b, _headers_b = _create_tutor_scope(db_session)

    res = client.get(
        f"/api/v1/microconcepts/subjects/{subject_b.id}",
        params={"term_id": str(term_b.id)},
        headers=headers_a,
    )
    assert res.status_code == 403
