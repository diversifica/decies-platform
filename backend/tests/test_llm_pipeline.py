import uuid
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item
from app.models.knowledge import KnowledgeChunk, KnowledgeEntry
from app.models.llm_run import LLMRun, LLMRunStep
from app.models.microconcept import MicroConcept
from app.models.role import Role
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User
from app.pipelines.processing import process_content_upload

client = TestClient(app)

# --- Mocks ---

MOCK_PDF_TEXT = "This is a test PDF content about Math. Chapter 1: Algebra. Algebra is fun."
MOCK_E2_RESPONSE = {
    "summary": "Summary of Math",
    "chunks": ["Chunk 1: Algebra is fun.", "Chunk 2: More text."],
}
MOCK_E4_RESPONSE = {
    "items": [
        {
            "type": "multiple_choice",
            "stem": "What is fun?",
            "options": ["Algebra", "Nothing"],
            "correct_answer": "Algebra",
            "explanation": "Because it is.",
        }
    ]
}
MOCK_E3_RESPONSE_BASE = {
    "chunk_mappings": [],
    "quality": {"mapping_coverage": 1.0, "mapping_precision_hint": "high", "notes": ["ok"]},
}
MOCK_E5_RESPONSE_BASE = {
    "validated_items": [],
    "quality": {"kept": 0, "fixed": 0, "dropped": 0, "notes": ["ok"]},
}


@pytest.fixture
def db_session():
    # Manually create session
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_upload_fixture(db_session):
    role_tutor = db_session.query(Role).filter_by(name="tutor").first()
    if not role_tutor:
        role_tutor = Role(name="tutor")
        db_session.add(role_tutor)
        db_session.commit()

    user_id = uuid.uuid4()
    password = "pw"
    user = User(
        id=user_id,
        email=f"tutor_{user_id}@pipeline.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    db_session.add(user)
    db_session.flush()

    tutor = Tutor(user_id=user.id, display_name="Pipeline Tutor")
    db_session.add(tutor)
    db_session.flush()

    subject = Subject(name="Pipeline Math", tutor_id=user.id)
    db_session.add(subject)
    db_session.flush()

    ac_year = AcademicYear(
        name=f"2026-{user_id}",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )
    db_session.add(ac_year)
    db_session.flush()

    term = Term(academic_year_id=ac_year.id, code="PT1", name="Pipeline Term 1")
    db_session.add(term)
    db_session.flush()

    mc_1 = MicroConcept(
        subject_id=subject.id,
        term_id=term.id,
        code="PIPE_MC_001",
        name="Algebra",
        description="...",
        active=True,
    )
    mc_2 = MicroConcept(
        subject_id=subject.id,
        term_id=term.id,
        code="PIPE_MC_002",
        name="Funciones",
        description="...",
        active=True,
    )
    db_session.add_all([mc_1, mc_2])
    db_session.flush()

    unique_suffix = str(uuid.uuid4())
    upload = ContentUpload(
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        upload_type=ContentUploadType.pdf,
        storage_uri=f"mock/path/test_{unique_suffix}.pdf",
        file_name=f"test_{unique_suffix}.pdf",
        mime_type="application/pdf",
        page_count=1,
    )
    db_session.add(upload)
    db_session.commit()

    return {
        "user": user,
        "password": password,
        "tutor": tutor,
        "subject": subject,
        "term": term,
        "microconcepts": (mc_1, mc_2),
        "upload": upload,
    }


def test_process_pipeline_success(db_session):
    # 1. Setup Data (Tutor, Upload)
    role_tutor = db_session.query(Role).filter_by(name="tutor").first()
    if not role_tutor:
        role_tutor = Role(name="tutor")
        db_session.add(role_tutor)
        db_session.commit()

    user_id = uuid.uuid4()
    password = "pw"
    user = User(
        id=user_id,
        email=f"tutor_{user_id}@pipeline.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role_tutor.id,
    )
    db_session.add(user)
    db_session.flush()

    tutor = Tutor(user_id=user.id, display_name="Pipeline Tutor")
    db_session.add(tutor)
    db_session.flush()

    subject = Subject(name="Pipeline Math", tutor_id=user.id)
    db_session.add(subject)

    ac_year = AcademicYear(name=f"2026-{user_id}", start_date="2026-01-01", end_date="2026-12-31")
    db_session.add(ac_year)
    db_session.flush()

    term = Term(academic_year_id=ac_year.id, code="PT1", name="Pipeline Term 1")
    db_session.add(term)
    db_session.flush()

    mc_1 = MicroConcept(
        subject_id=subject.id,
        term_id=term.id,
        code="PIPE_MC_001",
        name="Algebra",
        description="...",
        active=True,
    )
    mc_2 = MicroConcept(
        subject_id=subject.id,
        term_id=term.id,
        code="PIPE_MC_002",
        name="Funciones",
        description="...",
        active=True,
    )
    db_session.add_all([mc_1, mc_2])
    db_session.flush()

    unique_suffix = str(uuid.uuid4())
    upload = ContentUpload(
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        upload_type=ContentUploadType.pdf,
        storage_uri=f"mock/path/test_{unique_suffix}.pdf",
        file_name=f"test_{unique_suffix}.pdf",
        mime_type="application/pdf",
        page_count=1,
    )
    db_session.add(upload)
    db_session.commit()

    upload_id = upload.id

    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": user.email, "password": password},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Set Fake API Key for LLM Service Check
    settings.OPENAI_API_KEY = "fake-key"

    # 2. Mock External Services
    with (
        patch("app.pipelines.processing.extract_text_from_pdf", return_value=MOCK_PDF_TEXT),
        patch("app.pipelines.processing.os.path.exists", return_value=True),
        patch("app.services.llm_service.openai.OpenAI") as mock_openai,
    ):
        # Setup OpenAI Mock responses
        # E2 call
        mock_instance = mock_openai.return_value

        # We need to simulate TWO calls to create().
        # side_effect list: first call returns E2, second call returns E3, then E4 (for each chunk).
        # We have 2 chunks in E2 mock -> so 1 E2 call + 1 E3 call + 2 E4 calls = 4 calls total.

        # Mock Response Object
        def create_mock_response(content_dict):
            import json

            mock_msg = MagicMock()
            mock_msg.message.content = json.dumps(content_dict)
            mock_choice = MagicMock()
            mock_choice.choices = [mock_msg]
            return mock_choice

        mock_e3_response = {
            **MOCK_E3_RESPONSE_BASE,
            "chunk_mappings": [
                {
                    "chunk_index": 0,
                    "microconcept_match": {
                        "microconcept_id": str(mc_1.id),
                        "microconcept_code": mc_1.code,
                        "microconcept_name": mc_1.name,
                    },
                    "confidence": 0.9,
                    "reason": "Algebra",
                },
                {
                    "chunk_index": 1,
                    "microconcept_match": {
                        "microconcept_id": str(mc_2.id),
                        "microconcept_code": mc_2.code,
                        "microconcept_name": mc_2.name,
                    },
                    "confidence": 0.9,
                    "reason": "Funciones",
                },
            ],
        }

        mock_instance.chat.completions.create.side_effect = [
            create_mock_response(MOCK_E2_RESPONSE),  # E2
            create_mock_response(mock_e3_response),  # E3
            create_mock_response(MOCK_E4_RESPONSE),  # E4 for Chunk 1
            create_mock_response(MOCK_E4_RESPONSE),  # E4 for Chunk 2
            create_mock_response(
                {
                    **MOCK_E5_RESPONSE_BASE,
                    "validated_items": [
                        {
                            "index": 0,
                            "status": "ok",
                            "reason": "ok",
                            "item": {
                                "item_type": "mcq",
                                "stem": "What is fun?",
                                "options": ["Algebra", "Nothing"],
                                "correct_answer": "Algebra",
                                "explanation": "Because it is.",
                                "difficulty": 1.0,
                                "microconcept_ref": {
                                    "microconcept_id": str(mc_1.id),
                                    "microconcept_code": mc_1.code,
                                    "microconcept_name": mc_1.name,
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
                                "stem": "What is fun?",
                                "options": ["Algebra", "Nothing"],
                                "correct_answer": "Algebra",
                                "explanation": "Because it is.",
                                "difficulty": 1.0,
                                "microconcept_ref": {
                                    "microconcept_id": str(mc_2.id),
                                    "microconcept_code": mc_2.code,
                                    "microconcept_name": mc_2.name,
                                },
                                "source_chunk_index": 1,
                            },
                        },
                    ],
                    "quality": {"kept": 2, "fixed": 0, "dropped": 0, "notes": ["ok"]},
                }
            ),  # E5
        ]

        # 3. Trigger Endpoint
        response = client.post(f"/api/v1/content/uploads/{upload_id}/process", headers=headers)
        assert response.status_code == 202

        # 4. Verify Background Execution
        # Reload DB session to see changes
        db_session.expire_all()

        # Check KnowledgeEntry
        entry = db_session.query(KnowledgeEntry).filter_by(content_upload_id=upload_id).first()
        assert entry is not None
        assert entry.summary == "Summary of Math"

        # Check Chunks
        chunks = db_session.query(KnowledgeChunk).filter_by(knowledge_entry_id=entry.id).all()
        assert len(chunks) == 2
        assert {c.microconcept_id for c in chunks} == {mc_1.id, mc_2.id}

        # Check Items
        items = db_session.query(Item).filter_by(content_upload_id=upload_id).all()
        assert len(items) == 2
        assert items[0].stem == "What is fun?"
        assert all(item.microconcept_id is not None for item in items)
        assert {item.microconcept_id for item in items} == {mc_1.id, mc_2.id}

        microconcepts = (
            db_session.query(MicroConcept)
            .filter(MicroConcept.subject_id == subject.id, MicroConcept.term_id == term.id)
            .all()
        )
        assert len(microconcepts) >= 2

        # 5. Verify GET /items Endpoint
        response_items = client.get(f"/api/v1/content/uploads/{upload_id}/items", headers=headers)
        assert response_items.status_code == 200
        data = response_items.json()
        assert len(data) == 2
        assert data[0]["stem"] == "What is fun?"
        assert "correct_answer" in data[0]


def test_pipeline_segmentation_merges_chunks(db_session):
    fx = _create_upload_fixture(db_session)
    upload_id = fx["upload"].id

    settings.OPENAI_API_KEY = "fake-key"

    long_text = ("A" * 60) + "\n\n" + ("B" * 60) + "\n\n" + ("C" * 60)

    def create_mock_response(content_dict):
        import json

        mock_msg = MagicMock()
        mock_msg.message.content = json.dumps(content_dict)
        mock_choice = MagicMock()
        mock_choice.choices = [mock_msg]
        return mock_choice

    e2_segment_0 = {"summary": "S0", "chunks": ["C0"], "quality": {"hallucination_risk": "high"}}
    e2_segment_1 = {"summary": "S1", "chunks": ["C1"]}
    e2_segment_2 = {"summary": "S2", "chunks": ["C2"]}

    with (
        patch("app.pipelines.processing.extract_text_from_pdf", return_value=long_text),
        patch("app.pipelines.processing.os.path.exists", return_value=True),
        patch("app.pipelines.processing.E2_SEGMENT_MAX_CHARS", 70),
        patch("app.pipelines.processing.E2_SEGMENT_MIN_CHARS", 10),
        patch("app.services.llm_service.openai.OpenAI") as mock_openai,
    ):
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            create_mock_response(e2_segment_0),
            create_mock_response(e2_segment_1),
            create_mock_response(e2_segment_2),
        ]

        process_content_upload(db_session, upload_id)

        db_session.expire_all()
        entry = db_session.query(KnowledgeEntry).filter_by(content_upload_id=upload_id).first()
        assert entry is not None
        assert entry.structure_json["segments_count"] == 3
        assert entry.structure_json["chunks_count"] == 3

        chunks = (
            db_session.query(KnowledgeChunk)
            .filter_by(knowledge_entry_id=entry.id)
            .order_by(KnowledgeChunk.index.asc())
            .all()
        )
        assert [c.index for c in chunks] == [0, 1, 2]
        assert [c.content for c in chunks] == ["C0", "C1", "C2"]


def test_pipeline_retries_e2_and_logs_attempts(db_session):
    fx = _create_upload_fixture(db_session)
    upload_id = fx["upload"].id

    settings.OPENAI_API_KEY = "fake-key"

    def create_mock_response(content_dict):
        import json

        mock_msg = MagicMock()
        mock_msg.message.content = json.dumps(content_dict)
        mock_choice = MagicMock()
        mock_choice.choices = [mock_msg]
        return mock_choice

    e2_ok = {"summary": "S", "chunks": ["C"], "quality": {"hallucination_risk": "high"}}

    with (
        patch("app.pipelines.processing.extract_text_from_pdf", return_value="X" * 200),
        patch("app.pipelines.processing.os.path.exists", return_value=True),
        patch("app.services.llm_service.openai.OpenAI") as mock_openai,
    ):
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            RuntimeError("boom"),
            create_mock_response(e2_ok),
        ]

        process_content_upload(db_session, upload_id)

        runs = (
            db_session.query(LLMRun)
            .filter(LLMRun.content_upload_id == upload_id, LLMRun.step == LLMRunStep.E2_STRUCTURE)
            .order_by(LLMRun.created_at.asc())
            .all()
        )
        assert len(runs) == 2
        assert [r.attempt for r in runs] == [1, 2]
        assert runs[0].status == "failed"
        assert runs[1].status == "success"


def test_pipeline_e5_missing_validation_drops_item(db_session):
    fx = _create_upload_fixture(db_session)
    upload_id = fx["upload"].id
    mc_1, mc_2 = fx["microconcepts"]

    settings.OPENAI_API_KEY = "fake-key"

    def create_mock_response(content_dict):
        import json

        mock_msg = MagicMock()
        mock_msg.message.content = json.dumps(content_dict)
        mock_choice = MagicMock()
        mock_choice.choices = [mock_msg]
        return mock_choice

    e2 = {
        "summary": "Summary",
        "chunks": ["Chunk 0", "Chunk 1"],
        "quality": {"hallucination_risk": "low", "coverage": 1.0, "coherence": 1.0},
    }
    e3 = {
        **MOCK_E3_RESPONSE_BASE,
        "chunk_mappings": [
            {
                "chunk_index": 0,
                "microconcept_match": {
                    "microconcept_id": str(mc_1.id),
                    "microconcept_code": mc_1.code,
                    "microconcept_name": mc_1.name,
                },
                "confidence": 0.9,
                "reason": "Algebra",
            },
            {
                "chunk_index": 1,
                "microconcept_match": {
                    "microconcept_id": str(mc_2.id),
                    "microconcept_code": mc_2.code,
                    "microconcept_name": mc_2.name,
                },
                "confidence": 0.9,
                "reason": "Funciones",
            },
        ],
    }

    e4_items = {
        "items": [
            {
                "type": "multiple_choice",
                "stem": "Q1",
                "options": ["A", "B"],
                "correct_answer": "A",
                "explanation": "E",
            },
            {
                "type": "multiple_choice",
                "stem": "Q2",
                "options": ["A", "B"],
                "correct_answer": "A",
                "explanation": "E",
            },
        ]
    }

    e5 = {
        **MOCK_E5_RESPONSE_BASE,
        "validated_items": [
            {
                "index": 0,
                "status": "ok",
                "reason": "ok",
                "item": {
                    "item_type": "mcq",
                    "stem": "Q1",
                    "options": ["A", "B"],
                    "correct_answer": "A",
                    "explanation": "E",
                    "difficulty": 1.0,
                    "microconcept_ref": {
                        "microconcept_id": str(mc_1.id),
                        "microconcept_code": mc_1.code,
                        "microconcept_name": mc_1.name,
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
                    "stem": "Q2",
                    "options": ["A", "B"],
                    "correct_answer": "A",
                    "explanation": "E",
                    "difficulty": 1.0,
                    "microconcept_ref": {
                        "microconcept_id": str(mc_1.id),
                        "microconcept_code": mc_1.code,
                        "microconcept_name": mc_1.name,
                    },
                    "source_chunk_index": 0,
                },
            },
            {
                "index": 2,
                "status": "ok",
                "reason": "ok",
                "item": {
                    "item_type": "mcq",
                    "stem": "Q1",
                    "options": ["A", "B"],
                    "correct_answer": "A",
                    "explanation": "E",
                    "difficulty": 1.0,
                    "microconcept_ref": {
                        "microconcept_id": str(mc_2.id),
                        "microconcept_code": mc_2.code,
                        "microconcept_name": mc_2.name,
                    },
                    "source_chunk_index": 1,
                },
            },
        ],
        "quality": {"kept": 3, "fixed": 0, "dropped": 1, "notes": ["ok"]},
    }

    with (
        patch("app.pipelines.processing.extract_text_from_pdf", return_value=MOCK_PDF_TEXT),
        patch("app.pipelines.processing.os.path.exists", return_value=True),
        patch("app.services.llm_service.openai.OpenAI") as mock_openai,
    ):
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.side_effect = [
            create_mock_response(e2),
            create_mock_response(e3),
            create_mock_response(e4_items),
            create_mock_response(e4_items),
            create_mock_response(e5),
        ]

        process_content_upload(db_session, upload_id)

        items = (
            db_session.query(Item)
            .filter_by(content_upload_id=upload_id)
            .order_by(Item.created_at.asc())
            .all()
        )
        assert len(items) == 4

        dropped = [
            it
            for it in items
            if it.validation_reason and "missing_validation" in it.validation_reason
        ]
        assert len(dropped) == 1
        assert dropped[0].validation_status == "drop"
        assert dropped[0].is_active is False
        assert sum(1 for it in items if it.is_active) == 3
