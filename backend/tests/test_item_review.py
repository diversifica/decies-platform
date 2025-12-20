import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.activity import ActivityType
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item, ItemType
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


def _get_or_create_role(db: Session, name: str) -> Role:
    role = db.query(Role).filter(Role.name.ilike(name)).first()
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


def test_tutor_can_toggle_item_active_and_student_sees_only_active(db_session: Session):
    role_tutor = _get_or_create_role(db_session, "tutor")
    role_student = _get_or_create_role(db_session, "student")

    password = "pw"
    uid = uuid.uuid4()

    tutor_user = User(
        id=uuid.uuid4(),
        email=f"tutor_items_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"student_items_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor Items")
    db_session.add(tutor)
    db_session.flush()

    year = AcademicYear(
        name=f"2025-2026-items-{uid}",
        start_date="2025-09-01",
        end_date="2026-06-30",
    )
    db_session.add(year)
    db_session.flush()

    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    subject = Subject(name=f"Subject Items {uid}", tutor_id=tutor_user.id)
    db_session.add_all([term, subject])
    db_session.flush()

    student = Student(user_id=student_user.id, subject_id=subject.id)
    db_session.add(student)

    mc = MicroConcept(
        subject_id=subject.id,
        term_id=term.id,
        code="MC-ITEMS",
        name="MC Items",
        description="",
        active=True,
    )
    db_session.add(mc)
    db_session.flush()

    upload = ContentUpload(
        id=uuid.uuid4(),
        file_name="items_review.pdf",
        storage_uri="/test/items_review.pdf",
        mime_type="application/pdf",
        upload_type=ContentUploadType.pdf,
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        page_count=1,
    )
    db_session.add(upload)
    db_session.flush()

    inactive_item = Item(
        id=uuid.uuid4(),
        content_upload_id=upload.id,
        microconcept_id=mc.id,
        type=ItemType.MCQ,
        stem="Pregunta inactiva",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="",
        difficulty=1,
        is_active=True,
    )
    active_item = Item(
        id=uuid.uuid4(),
        content_upload_id=upload.id,
        microconcept_id=mc.id,
        type=ItemType.MCQ,
        stem="Pregunta activa",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="",
        difficulty=1,
        is_active=True,
    )
    db_session.add_all([inactive_item, active_item])

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(id=uuid.uuid4(), code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)

    db_session.commit()

    tutor_headers = _login(tutor_user.email, password)
    student_headers = _login(student_user.email, password)

    items_tutor_res = client.get(
        f"/api/v1/content/uploads/{upload.id}/items", headers=tutor_headers
    )
    assert items_tutor_res.status_code == 200
    assert len(items_tutor_res.json()) == 2

    toggle_res = client.patch(
        f"/api/v1/content/uploads/{upload.id}/items/{inactive_item.id}",
        json={"is_active": False},
        headers=tutor_headers,
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    items_tutor_res2 = client.get(
        f"/api/v1/content/uploads/{upload.id}/items", headers=tutor_headers
    )
    assert items_tutor_res2.status_code == 200
    assert any(
        i["id"] == str(inactive_item.id) and i["is_active"] is False
        for i in items_tutor_res2.json()
    )

    items_student_res = client.get(
        f"/api/v1/content/uploads/{upload.id}/items", headers=student_headers
    )
    assert items_student_res.status_code == 200
    assert all(i["id"] != str(inactive_item.id) for i in items_student_res.json())
    assert any(i["id"] == str(active_item.id) for i in items_student_res.json())

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
    session_items_res = client.get(
        f"/api/v1/activities/sessions/{session_id}/items", headers=student_headers
    )
    assert session_items_res.status_code == 200
    assert len(session_items_res.json()) == 1
    assert session_items_res.json()[0]["id"] == str(active_item.id)
