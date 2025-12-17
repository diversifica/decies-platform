import uuid
from datetime import datetime

import pytest

from app.core.db import SessionLocal
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept
from app.models.recommendation import RecommendationInstance, RecommendationStatus
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.recommendation import TutorDecisionCreate
from app.services.recommendation_service import recommendation_service


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper to create context
@pytest.fixture
def context(db_session):
    # Ensure roles
    role_student = db_session.query(Role).filter_by(name="Student").first()
    if not role_student:
        role_student = Role(name="Student")
        db_session.add(role_student)

    role_tutor = db_session.query(Role).filter_by(name="Tutor").first()
    if not role_tutor:
        role_tutor = Role(name="Tutor")
        db_session.add(role_tutor)

    db_session.commit()

    # Create unique Users/Student/Tutor
    uid = uuid.uuid4()
    u_stu = User(
        id=uuid.uuid4(),
        email=f"s_{uid}@test.com",
        role_id=role_student.id,
        full_name="S",
        hashed_password="x",
    )
    db_session.add(u_stu)
    # Flush to ensure user exists for foreign key
    db_session.flush()
    student = Student(id=u_stu.id, user_id=u_stu.id)
    db_session.add(student)

    u_tut = User(
        id=uuid.uuid4(),
        email=f"t_{uid}@test.com",
        role_id=role_tutor.id,
        full_name="T",
        hashed_password="x",
    )
    db_session.add(u_tut)
    db_session.flush()
    tutor = Tutor(id=u_tut.id, user_id=u_tut.id, display_name="Tutor Test")
    db_session.add(tutor)

    # Academic Year
    year = AcademicYear(
        id=uuid.uuid4(),
        name=f"2024_{uid}",
        start_date=datetime.now(),
        end_date=datetime.now(),
    )
    db_session.add(year)

    # Subject/Term
    subject = Subject(id=uuid.uuid4(), name=f"Sub {uid}")
    db_session.add(subject)
    term = Term(
        id=uuid.uuid4(),
        name="Term 1",
        code="T1",
        start_date=datetime.now(),
        end_date=datetime.now(),
        academic_year_id=year.id,
    )
    db_session.add(term)

    db_session.commit()

    return {
        "student": student,
        "tutor": tutor,
        "subject": subject,
        "term": term,
    }


def test_generate_recommendations_low_accuracy(db_session, context):
    """Test R01: Low global accuracy generates recommendation"""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    # Insert bad metrics
    agg = MetricAggregate(
        student_id=student.id,
        scope_type="subject",
        scope_id=subject.id,  # Using subject scope
        accuracy=0.3,  # Low accuracy
        first_attempt_accuracy=0.2,
        median_response_time_ms=5000,
        hint_rate=0.5,
        window_start=datetime.now(),
        window_end=datetime.now(),
        computed_at=datetime.now(),
    )
    db_session.add(agg)
    db_session.commit()

    # Run Generation
    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )

    assert len(recs) > 0
    r01 = next((r for r in recs if r.rule_id == "R01"), None)
    assert r01 is not None
    assert r01.priority == "high"
    assert "accuracy" in [e.key for e in r01.evidence]


def test_generate_recommendations_at_risk_concept(db_session, context):
    """Test R11: At-risk microconcept generates recommendation"""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    # Create MicroConcept
    mc = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Difficult Concept", description="..."
    )
    db_session.add(mc)
    db_session.flush()

    # Insert 'at_risk' mastery
    ms = MasteryState(
        student_id=student.id,
        microconcept_id=mc.id,
        mastery_score=0.2,
        status="at_risk",
        updated_at=datetime.now(),
    )
    db_session.add(ms)
    db_session.commit()

    # Run Generation
    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )

    r11 = next((r for r in recs if r.rule_id == "R11"), None)
    assert r11 is not None
    assert r11.microconcept_id == mc.id
    assert r11.status == RecommendationStatus.PENDING


def test_tutor_decision(db_session, context):
    """Test accepting a recommendation"""
    student = context["student"]
    tutor = context["tutor"]

    # Create a recommendation directly
    rec = RecommendationInstance(
        student_id=student.id,
        rule_id="TEST",
        title="Test Rec",
        description="...",
        status=RecommendationStatus.PENDING,
    )
    db_session.add(rec)
    db_session.commit()

    # Tutor accepts
    decision_data = TutorDecisionCreate(
        decision="accepted", notes="Sounds good", tutor_id=tutor.id, recommendation_id=rec.id
    )

    # Apply
    # Using Service Directly
    recommendation_service.apply_tutor_decision(db_session, decision_data)
