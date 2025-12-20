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
from app.models.metric import MasteryState
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


def _login(email: str, password: str) -> dict[str, str]:
    res = client.post("/api/v1/login/access-token", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_e2e_05_review_schedule_flow(db_session: Session):
    """
    Covers: schedule (due) -> REVIEW -> responses -> recalculate -> tutor sees updated schedule.
    """
    uid = uuid.uuid4()
    password = "pw"

    role_tutor = _ensure_role(db_session, "Tutor")
    role_student = _ensure_role(db_session, "Student")

    tutor_user = User(
        id=uuid.uuid4(),
        email=f"t5_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"s5_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor E2E-05")
    student = Student(user_id=student_user.id)

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    subject = Subject(name=f"Subject E2E-05 {uid}", tutor_id=tutor_user.id)
    db_session.add_all([tutor, student, year, term, subject])
    db_session.flush()

    student.subject_id = subject.id
    db_session.flush()

    review_type = db_session.query(ActivityType).filter_by(code="REVIEW").first()
    if not review_type:
        review_type = ActivityType(id=uuid.uuid4(), code="REVIEW", name="Review", active=True)
        db_session.add(review_type)
        db_session.flush()

    now = datetime.utcnow()

    mc_due = MicroConcept(
        id=uuid.uuid4(),
        subject_id=subject.id,
        term_id=term.id,
        code="MC-DUE",
        name="Microconcepto Due",
        description="Due for review",
        active=True,
    )
    mc_later = MicroConcept(
        id=uuid.uuid4(),
        subject_id=subject.id,
        term_id=term.id,
        code="MC-LATER",
        name="Microconcepto Later",
        description="Not due yet",
        active=True,
    )
    db_session.add_all([mc_due, mc_later])
    db_session.flush()

    due_state = MasteryState(
        id=uuid.uuid4(),
        student_id=student.id,
        microconcept_id=mc_due.id,
        mastery_score=0.4,
        status="in_progress",
        last_practice_at=now - timedelta(days=10),
        recommended_next_review_at=now - timedelta(days=3),
        updated_at=now,
    )
    later_state = MasteryState(
        id=uuid.uuid4(),
        student_id=student.id,
        microconcept_id=mc_later.id,
        mastery_score=0.9,
        status="dominant",
        last_practice_at=now - timedelta(days=1),
        recommended_next_review_at=now + timedelta(days=20),
        updated_at=now,
    )
    db_session.add_all([due_state, later_state])

    upload = ContentUpload(
        id=uuid.uuid4(),
        file_name="e2e_05.pdf",
        storage_uri="/test/e2e_05.pdf",
        mime_type="application/pdf",
        upload_type=ContentUploadType.pdf,
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        page_count=1,
    )
    db_session.add(upload)
    db_session.flush()

    item_due = Item(
        id=uuid.uuid4(),
        content_upload_id=upload.id,
        microconcept_id=mc_due.id,
        type=ItemType.MCQ,
        stem="¿Pregunta due?",
        options=["a", "b", "c"],
        correct_answer="b",
        explanation="b",
        difficulty=1,
        is_active=True,
    )
    item_later = Item(
        id=uuid.uuid4(),
        content_upload_id=upload.id,
        microconcept_id=mc_later.id,
        type=ItemType.MCQ,
        stem="¿Pregunta later?",
        options=["1", "2", "3"],
        correct_answer="2",
        explanation="2",
        difficulty=1,
        is_active=True,
    )
    db_session.add_all([item_due, item_later])
    db_session.commit()

    tutor_headers = _login(tutor_user.email, password)
    student_headers = _login(student_user.email, password)

    session_res = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(review_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 2,
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
    session_items = items_res.json()
    assert len(session_items) >= 1
    assert session_items[0]["microconcept_id"] == str(mc_due.id)

    start_time = datetime.utcnow()
    end_time = datetime.utcnow()
    for raw in session_items[:2]:
        response_res = client.post(
            f"/api/v1/activities/sessions/{session_id}/responses",
            json={
                "student_id": str(student.id),
                "item_id": raw["id"],
                "subject_id": str(subject.id),
                "term_id": str(term.id),
                "topic_id": None,
                "microconcept_id": None,
                "activity_type_id": str(review_type.id),
                "is_correct": True,
                "duration_ms": 10000,
                "attempt_number": 1,
                "response_normalized": raw.get("correct_answer") or "x",
                "hint_used": None,
                "difficulty_at_time": None,
                "timestamp_start": start_time.isoformat(),
                "timestamp_end": end_time.isoformat(),
            },
            headers=student_headers,
        )
        assert response_res.status_code == 200

    end_res = client.post(f"/api/v1/activities/sessions/{session_id}/end", headers=student_headers)
    assert end_res.status_code == 200

    mastery_res = client.get(
        f"/api/v1/metrics/students/{student.id}/mastery",
        params={"subject_id": str(subject.id), "term_id": str(term.id)},
        headers=tutor_headers,
    )
    assert mastery_res.status_code == 200
    mastery_payload = mastery_res.json()
    due_row = next(state for state in mastery_payload if state["microconcept_id"] == str(mc_due.id))
    assert due_row["last_practice_at"] is not None
    assert due_row["recommended_next_review_at"] is not None
    assert datetime.fromisoformat(due_row["recommended_next_review_at"]) > now
