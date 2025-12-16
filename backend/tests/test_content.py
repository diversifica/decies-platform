import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.content import ContentUpload
from app.models.role import Role
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User

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
    role = db_session.query(Role).filter_by(name="Tutor").first()
    if not role:
        role = Role(name="Tutor")
        db_session.add(role)
        db_session.commit()

    # Create User/Tutor
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"tutor_{user_id}@test.com",
        hashed_password="pw",
        is_active=True,
        role_id=role.id,
    )
    db_session.add(user)
    db_session.flush()

    tutor = Tutor(user_id=user.id, display_name="Test Tutor")
    db_session.add(tutor)

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

    # 2. Perform Request
    # We mock the file upload
    file_content = b"fake pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {"subject_id": str(subject.id), "term_id": str(term.id), "upload_type": "pdf"}
    # Auth is mocked in router to pick first tutor.
    # So it should pick our tutor (or another if exists).
    response = client.post("/api/v1/content/uploads", files=files, data=data)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["file_name"] == "test.pdf"
    assert "id" in json_resp

    # 3. Verify DB
    record = db_session.query(ContentUpload).filter_by(id=uuid.UUID(json_resp["id"])).first()
    assert record is not None
    assert record.tutor_id == tutor.id


def test_upload_content_missing_fields():
    response = client.post("/api/v1/content/uploads", data={})
    assert response.status_code == 422
