import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.main import app
from app.models.activity import ActivitySession, ActivitySessionItem, ActivityType
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item, ItemType
from app.models.metric import MasteryState
from app.models.microconcept import MicroConcept
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term
from app.models.tutor import Tutor

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


def test_create_activity_session_adaptive_selection_prioritizes_at_risk(db_session):
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
    tutor = db_session.query(Tutor).first()
    assert subject is not None
    assert term is not None
    assert activity_type is not None
    assert tutor is not None

    microconcepts = (
        db_session.query(MicroConcept)
        .filter(MicroConcept.subject_id == subject.id, MicroConcept.term_id == term.id)
        .order_by(MicroConcept.code.asc())
        .limit(3)
        .all()
    )
    assert len(microconcepts) == 3

    upload = ContentUpload(
        id=uuid.uuid4(),
        file_name="adaptive_selection_test.pdf",
        storage_uri="/test/adaptive_selection_test.pdf",
        mime_type="application/pdf",
        upload_type=ContentUploadType.pdf,
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        page_count=1,
    )
    db_session.add(upload)
    db_session.flush()

    for idx, mc in enumerate(microconcepts):
        for j in range(3):
            item = Item(
                id=uuid.uuid4(),
                content_upload_id=upload.id,
                microconcept_id=mc.id,
                type=ItemType.MCQ,
                stem=f"Pregunta adaptativa {idx}-{j}",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="",
                difficulty=1,
                is_active=True,
            )
            db_session.add(item)

    # Mastery setup:
    # - First microconcept at_risk
    # - Second in_progress
    # - Third dominant (should be de-prioritized)
    now = datetime.utcnow()
    statuses = ["at_risk", "in_progress", "dominant"]
    scores = [0.2, 0.6, 0.9]
    for mc, status, score in zip(microconcepts, statuses, scores, strict=True):
        existing = (
            db_session.query(MasteryState)
            .filter(MasteryState.student_id == student.id, MasteryState.microconcept_id == mc.id)
            .first()
        )
        if existing:
            existing.status = status
            existing.mastery_score = score
            existing.updated_at = now
            existing.last_practice_at = now
        else:
            db_session.add(
                MasteryState(
                    id=uuid.uuid4(),
                    student_id=student.id,
                    microconcept_id=mc.id,
                    mastery_score=score,
                    status=status,
                    last_practice_at=now,
                    updated_at=now,
                    metrics_version="V1",
                )
            )

    db_session.commit()

    response = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(activity_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 6,
            "content_upload_id": str(upload.id),
            "device_type": "web",
        },
        headers=headers,
    )

    assert response.status_code == 200
    session_id = uuid.UUID(response.json()["id"])

    selected = (
        db_session.query(Item)
        .join(ActivitySessionItem, ActivitySessionItem.item_id == Item.id)
        .filter(ActivitySessionItem.session_id == session_id)
        .order_by(ActivitySessionItem.order_index.asc())
        .all()
    )
    assert len(selected) == 6
    selected_microconcepts = [i.microconcept_id for i in selected]

    assert microconcepts[0].id in selected_microconcepts[:3]
    assert microconcepts[1].id in selected_microconcepts[:3]

    counts: dict[uuid.UUID, int] = {}
    for mcid in selected_microconcepts:
        assert mcid is not None
        counts[mcid] = counts.get(mcid, 0) + 1

    assert max(counts.values()) <= 2


def test_submit_activity_session_feedback(db_session):
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

    session_res = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(activity_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 3,
            "device_type": "web",
        },
        headers=headers,
    )
    assert session_res.status_code == 200
    session_id = uuid.UUID(session_res.json()["id"])

    end_res = client.post(f"/api/v1/activities/sessions/{session_id}/end", headers=headers)
    assert end_res.status_code == 200

    feedback_res = client.post(
        f"/api/v1/activities/sessions/{session_id}/feedback",
        json={"rating": 4, "text": "Me gustó la actividad."},
        headers=headers,
    )
    assert feedback_res.status_code == 200

    session = db_session.get(ActivitySession, session_id)
    assert session is not None
    assert session.feedback_rating == 4
    assert session.feedback_text == "Me gustó la actividad."
    assert session.feedback_submitted_at is not None
