import uuid
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.activity import ActivityType
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item, ItemType
from app.models.microconcept import MicroConcept, MicroConceptPrerequisite
from app.models.recommendation import RecommendationInstance
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


def test_e2e_03_prerequisites_r05_and_cloze_flow(db_session: Session):
    uid = uuid.uuid4()
    password = "pw"

    role_tutor = _ensure_role(db_session, "Tutor")
    role_student = _ensure_role(db_session, "Student")

    tutor_user = User(
        id=uuid.uuid4(),
        email=f"t3_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"s3_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor E2E-03")
    student = Student(user_id=student_user.id)
    db_session.add_all([tutor, student])
    db_session.flush()

    year = AcademicYear(
        name=f"2025-2026-{uid}",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 6, 30),
    )
    db_session.add(year)
    db_session.flush()

    term = Term(academic_year_id=year.id, code="T1", name="Term 1")
    subject = Subject(name=f"Math E2E-03 {uid}", tutor_id=tutor_user.id)
    db_session.add_all([term, subject])
    db_session.flush()

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(id=uuid.uuid4(), code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)

    cloze_type = db_session.query(ActivityType).filter_by(code="CLOZE").first()
    if not cloze_type:
        cloze_type = ActivityType(id=uuid.uuid4(), code="CLOZE", name="Cloze", active=True)
        db_session.add(cloze_type)

    db_session.commit()

    prereq_mc = MicroConcept(
        id=uuid.uuid4(),
        subject_id=subject.id,
        term_id=term.id,
        code="MC-PREREQ",
        name="Prerequisite",
        description="Prerequisite concept",
        active=True,
    )
    target_mc = MicroConcept(
        id=uuid.uuid4(),
        subject_id=subject.id,
        term_id=term.id,
        code="MC-TARGET",
        name="Target",
        description="Target concept",
        active=True,
    )
    db_session.add_all([prereq_mc, target_mc])
    db_session.flush()

    db_session.add(
        MicroConceptPrerequisite(
            id=uuid.uuid4(),
            microconcept_id=target_mc.id,
            prerequisite_microconcept_id=prereq_mc.id,
        )
    )

    upload = ContentUpload(
        id=uuid.uuid4(),
        file_name="e2e_03.pdf",
        storage_uri="/test/e2e_03.pdf",
        mime_type="application/pdf",
        upload_type=ContentUploadType.pdf,
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        page_count=1,
    )
    db_session.add(upload)
    db_session.flush()

    target_item = Item(
        id=uuid.uuid4(),
        content_upload_id=upload.id,
        microconcept_id=target_mc.id,
        type=ItemType.MCQ,
        stem="¿Cuánto es 2+2?",
        options=["1", "2", "3", "4"],
        correct_answer="4",
        explanation="2+2=4.",
        difficulty=1,
        is_active=True,
    )
    prereq_cloze = Item(
        id=uuid.uuid4(),
        content_upload_id=upload.id,
        microconcept_id=prereq_mc.id,
        type=ItemType.CLOZE,
        stem="Completa: 2 + 2 = ____",
        options={"placeholder": "____"},
        correct_answer="4",
        explanation="2+2=4.",
        difficulty=1,
        is_active=True,
    )
    db_session.add_all([target_item, prereq_cloze])
    db_session.commit()

    tutor_headers = _login(tutor_user.email, password)
    student_headers = _login(student_user.email, password)

    # 1) QUIZ session on target item -> incorrect -> end session -> metrics updated.
    # R05 should appear based on prerequisite reinforcement.
    quiz_session_res = client.post(
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
    assert quiz_session_res.status_code == 200
    quiz_session_id = quiz_session_res.json()["id"]

    quiz_items_res = client.get(
        f"/api/v1/activities/sessions/{quiz_session_id}/items", headers=student_headers
    )
    assert quiz_items_res.status_code == 200
    assert len(quiz_items_res.json()) == 1
    assert quiz_items_res.json()[0]["id"] == str(target_item.id)

    start_time = datetime.utcnow()
    end_time = datetime.utcnow()
    resp_res = client.post(
        f"/api/v1/activities/sessions/{quiz_session_id}/responses",
        json={
            "student_id": str(student.id),
            "item_id": str(target_item.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "microconcept_id": None,
            "activity_type_id": str(quiz_type.id),
            "is_correct": False,
            "duration_ms": 1000,
            "attempt_number": 1,
            "response_normalized": "1",
            "hint_used": None,
            "difficulty_at_time": None,
            "timestamp_start": start_time.isoformat(),
            "timestamp_end": end_time.isoformat(),
        },
        headers=student_headers,
    )
    assert resp_res.status_code == 200
    assert resp_res.json()["is_correct"] is False

    end_res = client.post(
        f"/api/v1/activities/sessions/{quiz_session_id}/end", headers=student_headers
    )
    assert end_res.status_code == 200

    recs_res = client.get(
        f"/api/v1/recommendations/students/{student.id}",
        params={"subject_id": str(subject.id), "term_id": str(term.id), "status_filter": "pending"},
        headers=tutor_headers,
    )
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert any(r["rule_id"] == "R05" for r in recs)

    # Ensure at least one R05 is tied to the prerequisite microconcept.
    db_session.expire_all()
    db_recs = (
        db_session.query(RecommendationInstance)
        .filter(
            RecommendationInstance.student_id == student.id, RecommendationInstance.rule_id == "R05"
        )
        .all()
    )
    assert any(r.microconcept_id == prereq_mc.id for r in db_recs)

    # 2) CLOZE session works end-to-end and backend grades response.
    cloze_session_res = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(cloze_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 1,
            "content_upload_id": str(upload.id),
            "device_type": "web",
        },
        headers=student_headers,
    )
    assert cloze_session_res.status_code == 200
    cloze_session_id = cloze_session_res.json()["id"]

    cloze_items_res = client.get(
        f"/api/v1/activities/sessions/{cloze_session_id}/items", headers=student_headers
    )
    assert cloze_items_res.status_code == 200
    assert len(cloze_items_res.json()) == 1
    assert cloze_items_res.json()[0]["type"] == ItemType.CLOZE.value

    start_time = datetime.utcnow()
    end_time = datetime.utcnow()
    cloze_resp_res = client.post(
        f"/api/v1/activities/sessions/{cloze_session_id}/responses",
        json={
            "student_id": str(student.id),
            "item_id": str(prereq_cloze.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "microconcept_id": None,
            "activity_type_id": str(cloze_type.id),
            "is_correct": False,
            "duration_ms": 1000,
            "attempt_number": 1,
            "response_normalized": "4",
            "hint_used": None,
            "difficulty_at_time": None,
            "timestamp_start": start_time.isoformat(),
            "timestamp_end": end_time.isoformat(),
        },
        headers=student_headers,
    )
    assert cloze_resp_res.status_code == 200
    assert cloze_resp_res.json()["is_correct"] is True
