import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app
from app.models.content import ContentUpload
from app.models.role import Role
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User
from app.routers.content import run_pipeline_task

client = TestClient(app)

# Fixture to setup data
# Since we are running against the dev DB (or test DB if configured), we should be careful.
# Ideally use a separate test DB, but for Sprint 0/Dev local we use the running one.
# For simplicity in this environment, I'll attempt to insert data into the running DB.
# BUT pytest usually uses a separate session/transaction.
# I'll rely on the existing pytest setup if it exists (conftest.py).
# Checking list_dir showed 'tests' has 2 children. likely conftest.py or test_main.py.

# I'll include a simple setup in the test function for now, assuming DB is accessible.


@pytest.fixture
def db_session():
    # Manually create session
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_upload_content_success(db_session: Session):
    # 1. Setup Data
    # Create Role
    role = db_session.query(Role).filter_by(name="tutor").first()
    if not role:
        role = Role(name="tutor")
        db_session.add(role)
        db_session.commit()

    # Create User/Tutor
    user_id = uuid.uuid4()
    password = "pw"
    user = User(
        id=user_id,
        email=f"tutor_{user_id}@test.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role.id,
    )
    db_session.add(user)
    db_session.flush()

    tutor = Tutor(user_id=user.id, display_name="Test Tutor")
    db_session.add(tutor)
    db_session.flush()

    # Create Academic Year & Term
    ac_year = AcademicYear(
        name=f"2025-2026-{user_id}", start_date="2025-09-01", end_date="2026-06-30"
    )
    db_session.add(ac_year)
    db_session.flush()

    term = Term(academic_year_id=ac_year.id, code="T1", name="Term 1")
    db_session.add(term)

    # Create Subject
    subject = Subject(name="Math", tutor_id=user.id)
    db_session.add(subject)

    db_session.commit()

    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": user.email, "password": password},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Perform Request
    # We mock the file upload
    file_content = b"fake pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {
        "subject_id": str(subject.id),
        "term_id": str(term.id),
        "upload_type": "pdf",
        "tutor_id": str(tutor.id),
    }
    response = client.post("/api/v1/content/uploads", files=files, data=data, headers=headers)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["file_name"] == "test.pdf"
    assert "id" in json_resp

    # 3. Verify DB
    record = db_session.query(ContentUpload).filter_by(id=uuid.UUID(json_resp["id"])).first()
    assert record is not None
    assert record.tutor_id == tutor.id


def test_upload_content_missing_fields():
    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": "tutor@decies.com", "password": "decies"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/content/uploads", data={}, headers=headers)
    assert response.status_code == 422


def test_process_upload_enqueues_when_async_enabled(db_session: Session):
    role = db_session.query(Role).filter_by(name="tutor").first()
    if not role:
        role = Role(name="tutor")
        db_session.add(role)
        db_session.commit()

    user_id = uuid.uuid4()
    password = "pw"
    user = User(
        id=user_id,
        email=f"tutor_{user_id}@test.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role.id,
    )
    db_session.add(user)
    db_session.flush()

    tutor = Tutor(user_id=user.id, display_name="Test Tutor")
    db_session.add(tutor)
    db_session.flush()

    ac_year = AcademicYear(
        name=f"2025-2026-{user_id}",
        start_date="2025-09-01",
        end_date="2026-06-30",
    )
    db_session.add(ac_year)
    db_session.flush()

    term = Term(academic_year_id=ac_year.id, code="T1", name="Term 1")
    db_session.add(term)

    subject = Subject(name="Math", tutor_id=user.id)
    db_session.add(subject)

    db_session.commit()

    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": user.email, "password": password},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_content = b"fake pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {
        "subject_id": str(subject.id),
        "term_id": str(term.id),
        "upload_type": "pdf",
        "tutor_id": str(tutor.id),
    }
    response = client.post("/api/v1/content/uploads", files=files, data=data, headers=headers)
    assert response.status_code == 201
    upload_id = response.json()["id"]

    prev = settings.ASYNC_QUEUE_ENABLED
    settings.ASYNC_QUEUE_ENABLED = True
    try:
        with patch(
            "app.routers.content.enqueue_upload_processing",
            return_value="job-123",
        ) as mocked:
            process_res = client.post(
                f"/api/v1/content/uploads/{upload_id}/process",
                headers=headers,
            )
            assert process_res.status_code == 202
            payload = process_res.json()
            assert payload["job_id"] == "job-123"
            mocked.assert_called_once()

        db_session.expire_all()
        upload = db_session.query(ContentUpload).filter_by(id=uuid.UUID(upload_id)).first()
        assert upload is not None
        assert upload.processing_status == "queued"
        assert upload.processing_job_id == "job-123"
        assert upload.processing_error is None
    finally:
        settings.ASYNC_QUEUE_ENABLED = prev


def test_run_pipeline_task_updates_processing_status_success(db_session: Session):
    role = db_session.query(Role).filter_by(name="tutor").first()
    if not role:
        role = Role(name="tutor")
        db_session.add(role)
        db_session.commit()

    user_id = uuid.uuid4()
    password = "pw"
    user = User(
        id=user_id,
        email=f"tutor_{user_id}@test.com",
        hashed_password=get_password_hash(password),
        is_active=True,
        role_id=role.id,
    )
    db_session.add(user)
    db_session.flush()

    tutor = Tutor(user_id=user.id, display_name="Test Tutor")
    db_session.add(tutor)
    db_session.flush()

    ac_year = AcademicYear(
        name=f"2025-2026-{user_id}",
        start_date="2025-09-01",
        end_date="2026-06-30",
    )
    db_session.add(ac_year)
    db_session.flush()

    term = Term(academic_year_id=ac_year.id, code="T1", name="Term 1")
    db_session.add(term)

    subject = Subject(name="Math", tutor_id=user.id)
    db_session.add(subject)

    db_session.commit()

    upload = ContentUpload(
        tutor_id=tutor.id,
        subject_id=subject.id,
        term_id=term.id,
        upload_type="pdf",
        storage_uri="mock/path/test.pdf",
        file_name="test.pdf",
        mime_type="application/pdf",
        page_count=1,
        processing_status="queued",
    )
    db_session.add(upload)
    db_session.commit()
    upload_id = upload.id

    with patch("app.routers.content.process_content_upload", return_value=None):
        run_pipeline_task(upload_id)

    db_session.expire_all()
    refreshed = db_session.query(ContentUpload).filter_by(id=upload_id).first()
    assert refreshed is not None
    assert refreshed.processing_status == "succeeded"
    assert refreshed.processing_error is None
    assert refreshed.processed_at is not None
