import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.main import app
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


def test_get_student_metrics(db_session):
    """Test getting student metrics"""
    student = db_session.query(Student).first()
    subject = db_session.query(Subject).first()
    term = db_session.query(Term).first()

    assert student is not None
    assert subject is not None
    assert term is not None

    response = client.get(
        f"/api/v1/metrics/students/{student.id}/metrics",
        params={"subject_id": str(subject.id), "term_id": str(term.id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "first_attempt_accuracy" in data
    assert "median_response_time_ms" in data
    assert "total_sessions" in data
    assert data["student_id"] == str(student.id)


def test_get_mastery_states(db_session):
    """Test getting mastery states for a student"""
    student = db_session.query(Student).first()
    subject = db_session.query(Subject).first()
    term = db_session.query(Term).first()

    response = client.get(
        f"/api/v1/metrics/students/{student.id}/mastery",
        params={"subject_id": str(subject.id), "term_id": str(term.id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Should have mastery states for all microconcepts
    if len(data) > 0:
        state = data[0]
        assert "microconcept_id" in state
        assert "microconcept_name" in state
        assert "mastery_score" in state
        assert "status" in state
        assert state["status"] in ["dominant", "in_progress", "at_risk"]


def test_recalculate_metrics(db_session):
    """Test manual metrics recalculation"""
    student = db_session.query(Student).first()
    subject = db_session.query(Subject).first()
    term = db_session.query(Term).first()

    response = client.post(
        "/api/v1/metrics/recalculate",
        params={
            "student_id": str(student.id),
            "subject_id": str(subject.id),
            "term_id": str(term.id),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "metrics_id" in data
    assert "mastery_states_count" in data
