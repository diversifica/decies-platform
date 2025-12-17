import pytest

from app.core.db import SessionLocal
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term
from app.services.metric_service import MetricService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def metric_service():
    return MetricService()


def test_mastery_score_calculation(db_session, metric_service):
    """Test mastery score calculation algorithm"""
    student = db_session.query(Student).first()
    subject = db_session.query(Subject).first()
    term = db_session.query(Term).first()

    # Calculate mastery states
    mastery_states = metric_service.calculate_mastery_states(
        db_session, student.id, subject.id, term.id
    )

    assert isinstance(mastery_states, list)

    for state in mastery_states:
        # Mastery score should be between 0 and 1
        assert 0.0 <= state.mastery_score <= 1.0

        # Status should match score thresholds
        if state.mastery_score >= 0.8:
            assert state.status == "dominant"
        elif state.mastery_score >= 0.5:
            assert state.status == "in_progress"
        else:
            assert state.status == "at_risk"


def test_metrics_with_no_events(db_session, metric_service):
    """Test metrics calculation when student has no learning events"""
    student = db_session.query(Student).first()
    subject = db_session.query(Subject).first()
    term = db_session.query(Term).first()

    # Calculate metrics for student with no events
    metrics = metric_service.calculate_student_metrics(db_session, student.id, subject.id, term.id)

    # Should return zero metrics, not error
    assert metrics.accuracy == 0.0
    assert metrics.error_rate == 1.0
    assert metrics.median_response_time_ms == 0


def test_mastery_status_thresholds(db_session, metric_service):
    """Test that mastery status correctly reflects score thresholds"""
    student = db_session.query(Student).first()
    subject = db_session.query(Subject).first()
    term = db_session.query(Term).first()

    mastery_states = metric_service.calculate_mastery_states(
        db_session, student.id, subject.id, term.id
    )

    for state in mastery_states:
        # Verify status matches documented thresholds
        if state.status == "dominant":
            assert state.mastery_score >= 0.8
        elif state.status == "in_progress":
            assert 0.5 <= state.mastery_score < 0.8
        elif state.status == "at_risk":
            assert state.mastery_score < 0.5


def test_recalculate_and_save(db_session, metric_service):
    """Test that recalculate_and_save_metrics persists data correctly"""
    student = db_session.query(Student).first()
    subject = db_session.query(Subject).first()
    term = db_session.query(Term).first()

    # Recalculate and save
    metrics, mastery_states = metric_service.recalculate_and_save_metrics(
        db_session, student.id, subject.id, term.id
    )

    # Verify metrics were saved
    assert metrics.id is not None
    assert metrics.computed_at is not None

    # Verify mastery states were saved
    for state in mastery_states:
        assert state.id is not None
        assert state.updated_at is not None
