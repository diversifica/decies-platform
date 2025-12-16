import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item
from app.models.knowledge import KnowledgeChunk, KnowledgeEntry
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User

client = TestClient(app)

# --- Mocks ---

MOCK_PDF_TEXT = "This is a test PDF content about Math. Chapter 1: Algebra. Algebra is fun."
MOCK_E2_RESPONSE = {
    "summary": "Summary of Math",
    "chunks": ["Chunk 1: Algebra is fun.", "Chunk 2: More text."]
}
MOCK_E4_RESPONSE = {
    "items": [
        {
            "type": "multiple_choice",
            "stem": "What is fun?",
            "options": ["Algebra", "Nothing"],
            "correct_answer": "Algebra",
            "explanation": "Because it is."
        }
    ]
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


def test_process_pipeline_success(db_session):
    # 1. Setup Data (Tutor, Upload)
    role_name = "Tutor_Pipeline"
    role_tutor = db_session.query(Role).filter_by(name=role_name).first()
    if not role_tutor:
        role_tutor = Role(name=role_name)
        db_session.add(role_tutor)
        db_session.commit()

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"tutor_{user_id}@pipeline.com",
        hashed_password="pw",
        is_active=True,
        role_id=role_tutor.id,
    )
    db_session.add(user)
    db_session.flush()

    tutor = Tutor(user_id=user.id, display_name="Pipeline Tutor")
    db_session.add(tutor)
    
    subject = Subject(name="Pipeline Math", tutor_id=user.id)
    db_session.add(subject)
    
    ac_year = AcademicYear(name=f"2026-{user_id}", start_date="2026-01-01", end_date="2026-12-31")
    db_session.add(ac_year)
    db_session.flush()
    
    term = Term(academic_year_id=ac_year.id, code="PT1", name="Pipeline Term 1")
    db_session.add(term)
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
        page_count=1
    )
    db_session.add(upload)
    db_session.commit()
    
    upload_id = upload.id
    
    # Set Fake API Key for LLM Service Check
    settings.OPENAI_API_KEY = "fake-key"

    # 2. Mock External Services
    with patch("app.pipelines.processing.extract_text_from_pdf", return_value=MOCK_PDF_TEXT) as mock_extract, \
         patch("app.pipelines.processing.os.path.exists", return_value=True), \
         patch("app.services.llm_service.openai.OpenAI") as mock_openai:
        
        # Setup OpenAI Mock responses
        # E2 call
        mock_instance = mock_openai.return_value
        
        # We need to simulate TWO calls to create(). 
        # side_effect list: first call returns E2, second call... returns E4 (for each chunk).
        # We have 2 chunks in E2 mock -> so 1 E2 call + 2 E4 calls = 3 calls total.
        
        # Mock Response Object
        def create_mock_response(content_dict):
            import json
            mock_msg = MagicMock()
            mock_msg.message.content = json.dumps(content_dict)
            mock_choice = MagicMock()
            mock_choice.choices = [mock_msg]
            return mock_choice

        mock_instance.chat.completions.create.side_effect = [
            create_mock_response(MOCK_E2_RESPONSE),      # E2
            create_mock_response(MOCK_E4_RESPONSE),      # E4 for Chunk 1
            create_mock_response(MOCK_E4_RESPONSE)       # E4 for Chunk 2
        ]
        
        # 3. Trigger Endpoint
        response = client.post(f"/api/v1/content/uploads/{upload_id}/process")
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
        
        # Check Items
        items = db_session.query(Item).filter_by(content_upload_id=upload_id).all()
        assert len(items) == 2
        assert items[0].stem == "What is fun?"
