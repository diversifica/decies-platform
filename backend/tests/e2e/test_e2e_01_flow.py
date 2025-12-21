import uuid
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.main import app
from app.models.activity import ActivityType
from app.models.item import Item
from app.models.microconcept import MicroConcept
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User

client = TestClient(app)

MOCK_PDF_TEXT = "Contenido de prueba de matemáticas: suma, resta y números enteros."
MOCK_E2_RESPONSE = {"summary": "Resumen", "chunks": ["Chunk 1", "Chunk 2"]}
MOCK_E3_RESPONSE = {
    "chunk_mappings": [
        {
            "chunk_index": 0,
            "microconcept_match": {
                "microconcept_id": None,
                "microconcept_code": None,
                "microconcept_name": None,
            },
            "confidence": 0.0,
            "reason": "low confidence",
        },
        {
            "chunk_index": 1,
            "microconcept_match": {
                "microconcept_id": None,
                "microconcept_code": None,
                "microconcept_name": None,
            },
            "confidence": 0.0,
            "reason": "low confidence",
        },
    ],
    "quality": {"mapping_coverage": 0.0, "mapping_precision_hint": "low", "notes": ["n/a"]},
}
MOCK_E5_RESPONSE = {
    "validated_items": [
        {
            "index": 0,
            "status": "ok",
            "reason": "ok",
            "item": {
                "item_type": "mcq",
                "stem": "¿Cuál es el resultado de 1+1?",
                "options": ["1", "2", "3", "4"],
                "correct_answer": "2",
                "explanation": "1+1=2.",
                "difficulty": 1.0,
                "microconcept_ref": {
                    "microconcept_id": None,
                    "microconcept_code": None,
                    "microconcept_name": None,
                },
                "source_chunk_index": 0,
            },
        },
        {
            "index": 1,
            "status": "ok",
            "reason": "ok",
            "item": {
                "item_type": "mcq",
                "stem": "¿Cuál es el resultado de 1+1?",
                "options": ["1", "2", "3", "4"],
                "correct_answer": "2",
                "explanation": "1+1=2.",
                "difficulty": 1.0,
                "microconcept_ref": {
                    "microconcept_id": None,
                    "microconcept_code": None,
                    "microconcept_name": None,
                },
                "source_chunk_index": 1,
            },
        },
    ],
    "quality": {"kept": 2, "fixed": 0, "dropped": 0, "notes": ["ok"]},
}
MOCK_E4_RESPONSE = {
    "items": [
        {
            "type": "multiple_choice",
            "stem": "¿Cuál es el resultado de 1+1?",
            "options": ["1", "2", "3", "4"],
            "correct_answer": "2",
            "explanation": "1+1=2.",
        }
    ]
}


@pytest.fixture
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_mock_response(content_dict: dict) -> MagicMock:
    import json

    mock_msg = MagicMock()
    mock_msg.message.content = json.dumps(content_dict)
    mock_choice = MagicMock()
    mock_choice.choices = [mock_msg]
    return mock_choice


def test_e2e_01_flow_content_to_report(db_session: Session):
    uid = uuid.uuid4()

    role_student = db_session.query(Role).filter_by(name="Student").first()
    if not role_student:
        role_student = Role(name="Student")
        db_session.add(role_student)

    role_tutor = db_session.query(Role).filter_by(name="Tutor").first()
    if not role_tutor:
        role_tutor = Role(name="Tutor")
        db_session.add(role_tutor)

    db_session.commit()

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

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor E2E")
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
    subject = Subject(name=f"Math E2E {uid}", tutor_id=tutor_user.id)
    db_session.add_all([term, subject])

    activity_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not activity_type:
        activity_type = ActivityType(code="QUIZ", name="Quiz", active=True)
        db_session.add(activity_type)

    db_session.commit()

    tutor_token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": tutor_user.email, "password": password},
    )
    assert tutor_token_res.status_code == 200
    tutor_headers = {"Authorization": f"Bearer {tutor_token_res.json()['access_token']}"}

    student_token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": student_user.email, "password": password},
    )
    assert student_token_res.status_code == 200
    student_headers = {"Authorization": f"Bearer {student_token_res.json()['access_token']}"}

    files = {"file": ("test.pdf", b"fake pdf", "application/pdf")}
    data = {
        "subject_id": str(subject.id),
        "term_id": str(term.id),
        "upload_type": "pdf",
        "tutor_id": str(tutor.id),
    }
    upload_res = client.post(
        "/api/v1/content/uploads", files=files, data=data, headers=tutor_headers
    )
    assert upload_res.status_code == 201
    upload_id = upload_res.json()["id"]

    settings.OPENAI_API_KEY = "fake-key"
    with (
        patch("app.pipelines.processing.extract_text_from_pdf", return_value=MOCK_PDF_TEXT),
        patch("app.pipelines.processing.os.path.exists", return_value=True),
        patch("app.services.llm_service.openai.OpenAI") as mock_openai,
    ):
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            _create_mock_response(MOCK_E2_RESPONSE),
            _create_mock_response(MOCK_E3_RESPONSE),
            _create_mock_response(MOCK_E4_RESPONSE),
            _create_mock_response(MOCK_E4_RESPONSE),
            _create_mock_response(MOCK_E5_RESPONSE),
        ]

        process_res = client.post(
            f"/api/v1/content/uploads/{upload_id}/process",
            headers=tutor_headers,
        )
        assert process_res.status_code == 202

    db_session.expire_all()

    microconcepts = (
        db_session.query(MicroConcept)
        .filter(MicroConcept.subject_id == subject.id, MicroConcept.term_id == term.id)
        .all()
    )
    assert any(mc.name == "General" for mc in microconcepts)

    items = db_session.query(Item).filter(Item.content_upload_id == uuid.UUID(upload_id)).all()
    assert len(items) >= 2
    assert all(item.microconcept_id is not None for item in items)

    session_res = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(activity_type.id),
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

    start_time = datetime.utcnow()
    end_time = datetime.utcnow()
    for item in items[:2]:
        response_res = client.post(
            f"/api/v1/activities/sessions/{session_id}/responses",
            json={
                "student_id": str(student.id),
                "item_id": str(item.id),
                "subject_id": str(subject.id),
                "term_id": str(term.id),
                "topic_id": None,
                "microconcept_id": None,
                "activity_type_id": str(activity_type.id),
                "is_correct": False,
                "duration_ms": 40000,
                "attempt_number": 1,
                "response_normalized": "x",
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

    metrics_res = client.get(
        f"/api/v1/metrics/students/{student.id}/metrics",
        params={"subject_id": str(subject.id), "term_id": str(term.id)},
        headers=tutor_headers,
    )
    assert metrics_res.status_code == 200
    metrics_payload = metrics_res.json()
    assert metrics_payload["accuracy"] < 0.5
    assert metrics_payload["median_response_time_ms"] > 30000

    mastery_res = client.get(
        f"/api/v1/metrics/students/{student.id}/mastery",
        params={"subject_id": str(subject.id), "term_id": str(term.id)},
        headers=tutor_headers,
    )
    assert mastery_res.status_code == 200
    mastery_payload = mastery_res.json()
    assert len(mastery_payload) >= 1
    assert any(state["total_events"] >= 1 for state in mastery_payload)

    recs_res = client.get(
        f"/api/v1/recommendations/students/{student.id}",
        params={"subject_id": str(subject.id), "term_id": str(term.id)},
        headers=tutor_headers,
    )
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) >= 1
    assert any(rec["rule_id"] == "R01" for rec in recs)

    r01 = next(rec for rec in recs if rec["rule_id"] == "R01")
    decision_res = client.post(
        f"/api/v1/recommendations/{r01['id']}/decision",
        json={
            "decision": "accepted",
            "notes": "OK",
            "tutor_id": str(tutor.id),
            "recommendation_id": r01["id"],
        },
        headers=tutor_headers,
    )
    assert decision_res.status_code == 200
    assert decision_res.json()["decision"] == "accepted"

    get_rec_res = client.get(f"/api/v1/recommendations/{r01['id']}", headers=tutor_headers)
    assert get_rec_res.status_code == 200
    assert get_rec_res.json()["status"] == "accepted"

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
    assert report["student_id"] == str(student.id)
    assert any(section["section_type"] == "mastery" for section in report["sections"])

    latest_res = client.get(
        f"/api/v1/reports/students/{student.id}/latest",
        params={"tutor_id": str(tutor.id), "subject_id": str(subject.id), "term_id": str(term.id)},
        headers=tutor_headers,
    )
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == report["id"]
