import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.activity import ActivitySession, ActivityType, LearningEvent
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item, ItemType
from app.models.microconcept import MicroConcept
from app.models.recommendation import (
    RecommendationInstance,
    RecommendationPriority,
    RecommendationStatus,
    TutorDecision,
)
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


def test_compute_recommendation_outcomes_creates_outcome(db_session: Session):
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

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor Outcomes")
    subject = Subject(name=f"Subject {uid}", tutor_id=tutor_user.id)
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

    microconcept = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="MC A", description="..."
    )
    db_session.add(microconcept)
    db_session.flush()

    upload = ContentUpload(
        tutor_id=tutor.id,
        student_id=student.id,
        subject_id=subject.id,
        term_id=term.id,
        topic_id=None,
        upload_type=ContentUploadType.pdf,
        storage_uri="file://test.pdf",
        file_name="test.pdf",
        mime_type="application/pdf",
        page_count=1,
    )
    db_session.add(upload)
    db_session.flush()

    item = Item(
        content_upload_id=upload.id,
        microconcept_id=microconcept.id,
        type=ItemType.MCQ,
        stem="2+2?",
        options={"choices": ["3", "4"]},
        correct_answer="4",
        explanation="2+2=4",
        difficulty=1,
        is_active=True,
    )
    db_session.add(item)
    db_session.flush()

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)
        db_session.flush()

    now = datetime.utcnow()
    decision_at = now - timedelta(days=20)
    window_days = 14

    session = ActivitySession(
        student_id=student.id,
        activity_type_id=quiz_type.id,
        subject_id=subject.id,
        term_id=term.id,
        topic_id=None,
        started_at=decision_at - timedelta(days=1),
        ended_at=decision_at - timedelta(days=1) + timedelta(minutes=5),
        status="completed",
        device_type="web",
    )
    db_session.add(session)
    db_session.flush()

    # Pre-window: mostly incorrect
    pre_start = decision_at - timedelta(days=window_days)
    for i in range(5):
        ts = pre_start + timedelta(days=i + 1)
        db_session.add(
            LearningEvent(
                student_id=student.id,
                session_id=session.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                microconcept_id=microconcept.id,
                activity_type_id=quiz_type.id,
                item_id=item.id,
                timestamp_start=ts,
                timestamp_end=ts + timedelta(seconds=10),
                duration_ms=10_000,
                attempt_number=1,
                response_normalized="3",
                is_correct=False,
                hint_used="none",
                difficulty_at_time=1,
            )
        )

    # Post-window: mostly correct
    post_end = decision_at + timedelta(days=window_days)
    for i in range(5):
        ts = decision_at + timedelta(days=i + 1)
        if ts >= post_end:
            ts = post_end - timedelta(hours=1)
        db_session.add(
            LearningEvent(
                student_id=student.id,
                session_id=session.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                microconcept_id=microconcept.id,
                activity_type_id=quiz_type.id,
                item_id=item.id,
                timestamp_start=ts,
                timestamp_end=ts + timedelta(seconds=10),
                duration_ms=10_000,
                attempt_number=1,
                response_normalized="4",
                is_correct=True,
                hint_used="none",
                difficulty_at_time=1,
            )
        )

    recommendation = RecommendationInstance(
        id=uuid.uuid4(),
        student_id=student.id,
        microconcept_id=microconcept.id,
        rule_id="R11",
        priority=RecommendationPriority.MEDIUM,
        status=RecommendationStatus.ACCEPTED,
        title="Refuerzo MC A",
        description="...",
        evaluation_window_days=window_days,
        generated_at=decision_at - timedelta(days=1),
        updated_at=decision_at,
    )
    db_session.add(recommendation)
    db_session.flush()

    decision = TutorDecision(
        id=uuid.uuid4(),
        recommendation_id=recommendation.id,
        tutor_id=tutor.id,
        decision="accepted",
        notes=None,
        decision_at=decision_at,
    )
    db_session.add(decision)
    db_session.commit()

    headers = _login(tutor_user.email, password)

    res = client.post(
        "/api/v1/recommendations/outcomes/compute",
        params={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
        },
        headers=headers,
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["created"] == 1
    assert payload["updated"] == 0
    assert payload["pending"] == 0
    assert len(payload["outcomes"]) == 1
    outcome = payload["outcomes"][0]
    assert outcome["recommendation_id"] == str(recommendation.id)
    assert outcome["success"] in {"true", "partial", "false"}
    assert outcome["delta_accuracy"] is not None
    assert outcome["delta_accuracy"] > 0
