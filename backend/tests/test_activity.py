import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.main import app
from app.models.activity import ActivityType
from app.models.item import Item
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_activity_session(db_session):
    """Test creating an activity session"""
    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": "student@decies.com", "password": "decies"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    student_id = uuid.UUID(me_res.json()["student_id"])

    student = db_session.get(Student, student_id)
    assert student is not None

    subject = db_session.get(Subject, student.subject_id)
    term = db_session.query(Term).filter_by(code="T1").first()
    activity_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()

    assert subject is not None
    assert term is not None
    assert activity_type is not None

    # Create session
    response = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(activity_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 5,
            "device_type": "web",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["student_id"] == str(student.id)


def test_record_learning_event(db_session):
    """Test recording a learning event"""
    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": "student@decies.com", "password": "decies"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    student_id = uuid.UUID(me_res.json()["student_id"])

    # Create a session first
    student = db_session.get(Student, student_id)
    assert student is not None

    subject = db_session.get(Subject, student.subject_id)
    term = db_session.query(Term).filter_by(code="T1").first()
    activity_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    item = db_session.query(Item).first()

    session_response = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(activity_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 5,
            "device_type": "web",
        },
        headers=headers,
    )
    session_id = session_response.json()["id"]

    # Record event
    start_time = datetime.utcnow()
    end_time = datetime.utcnow()

    response = client.post(
        f"/api/v1/activities/sessions/{session_id}/responses",
        json={
            "student_id": str(student.id),
            "item_id": str(item.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "microconcept_id": None,
            "activity_type_id": str(activity_type.id),
            "is_correct": True,
            "duration_ms": 5000,
            "attempt_number": 1,
            "response_normalized": "Test answer",
            "hint_used": None,
            "difficulty_at_time": None,
            "timestamp_start": start_time.isoformat(),
            "timestamp_end": end_time.isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["duration_ms"] == 5000


def test_end_session(db_session):
    """Test ending a session and triggering metrics recalculation"""
    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": "student@decies.com", "password": "decies"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    student_id = uuid.UUID(me_res.json()["student_id"])

    student = db_session.get(Student, student_id)
    assert student is not None

    subject = db_session.get(Subject, student.subject_id)
    term = db_session.query(Term).filter_by(code="T1").first()
    activity_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()

    # Create session
    session_response = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(activity_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 5,
            "device_type": "web",
        },
        headers=headers,
    )
    session_id = session_response.json()["id"]

    # End session
    response = client.post(f"/api/v1/activities/sessions/{session_id}/end", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["ended_at"] is not None


def test_list_activity_types(db_session):
    """Test listing activity types"""
    response = client.get("/api/v1/activities/activity-types")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # QUIZ, MATCH, REVIEW from seed
    assert any(t["code"] == "QUIZ" for t in data)
