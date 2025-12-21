import json
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
from app.models.item import Item, ItemType
from app.models.microconcept import MicroConcept
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User

client = TestClient(app)

MOCK_PDF_TEXT = "Contenido de prueba: suma, resta y números enteros."
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


@pytest.fixture
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_mock_response(content_dict: dict) -> MagicMock:
    mock_msg = MagicMock()
    mock_msg.message.content = json.dumps(content_dict)
    mock_choice = MagicMock()
    mock_choice.choices = [mock_msg]
    return mock_choice


def test_e2e_02_flow_match_and_feedback(db_session: Session):
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
        email=f"t2_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    student_user = User(
        id=uuid.uuid4(),
        email=f"s2_{uid}@example.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_student.id,
    )
    db_session.add_all([tutor_user, student_user])
    db_session.flush()

    tutor = Tutor(user_id=tutor_user.id, display_name="Tutor E2E-02")
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
    subject = Subject(name=f"Math E2E-02 {uid}", tutor_id=tutor_user.id)
    db_session.add_all([term, subject])
    db_session.flush()

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)

    match_type = db_session.query(ActivityType).filter_by(code="MATCH").first()
    if not match_type:
        match_type = ActivityType(code="MATCH", name="Match", active=True)
        db_session.add(match_type)

    microconcepts: list[MicroConcept] = []
    for i in range(4):
        microconcepts.append(
            MicroConcept(
                subject_id=subject.id,
                term_id=term.id,
                code=f"MC-E2E-02-{i + 1}",
                name=f"Concept {i + 1}",
                description=f"Description {i + 1}",
                active=True,
            )
        )
    db_session.add_all(microconcepts)
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

    pairs = [{"left": mc.name, "right": mc.description or mc.name} for mc in microconcepts]
    expected = {p["left"]: p["right"] for p in pairs}
    match_item = Item(
        id=uuid.uuid4(),
        content_upload_id=uuid.UUID(upload_id),
        microconcept_id=microconcepts[0].id,
        type=ItemType.MATCH,
        stem="Empareja cada concepto con su descripción",
        options={"pairs": pairs},
        correct_answer=json.dumps(expected, ensure_ascii=False),
        explanation="",
        difficulty=1,
        is_active=True,
    )
    db_session.add(match_item)
    db_session.commit()

    match_session_res = client.post(
        "/api/v1/activities/sessions",
        json={
            "student_id": str(student.id),
            "activity_type_id": str(match_type.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "item_count": 1,
            "content_upload_id": upload_id,
            "device_type": "web",
        },
        headers=student_headers,
    )
    assert match_session_res.status_code == 200
    match_session_id = match_session_res.json()["id"]

    match_items_res = client.get(
        f"/api/v1/activities/sessions/{match_session_id}/items", headers=student_headers
    )
    assert match_items_res.status_code == 200
    match_items = match_items_res.json()
    assert len(match_items) == 1
    assert match_items[0]["type"] == ItemType.MATCH.value

    match_options = match_items[0]["options"]
    assert isinstance(match_options, dict)
    submitted_pairs = match_options.get("pairs")
    assert isinstance(submitted_pairs, list)
    submitted = {p["left"]: p["right"] for p in submitted_pairs}

    start_time = datetime.utcnow()
    end_time = datetime.utcnow()
    response_res = client.post(
        f"/api/v1/activities/sessions/{match_session_id}/responses",
        json={
            "student_id": str(student.id),
            "item_id": match_items[0]["id"],
            "subject_id": str(subject.id),
            "term_id": str(term.id),
            "topic_id": None,
            "microconcept_id": None,
            "activity_type_id": str(match_type.id),
            "is_correct": False,
            "duration_ms": 2000,
            "attempt_number": 1,
            "response_normalized": json.dumps(submitted, ensure_ascii=False),
            "hint_used": None,
            "difficulty_at_time": None,
            "timestamp_start": start_time.isoformat(),
            "timestamp_end": end_time.isoformat(),
        },
        headers=student_headers,
    )
    assert response_res.status_code == 200
    assert response_res.json()["is_correct"] is True

    end_res = client.post(
        f"/api/v1/activities/sessions/{match_session_id}/end", headers=student_headers
    )
    assert end_res.status_code == 200

    feedback_text = "Me ha gustado el juego MATCH."
    feedback_res = client.post(
        f"/api/v1/activities/sessions/{match_session_id}/feedback",
        json={"rating": 5, "text": feedback_text},
        headers=student_headers,
    )
    assert feedback_res.status_code == 200

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
    feedback_section = next(
        (s for s in report["sections"] if s["section_type"] == "student_feedback"), None
    )
    assert feedback_section is not None
    assert feedback_text in feedback_section["content"]
