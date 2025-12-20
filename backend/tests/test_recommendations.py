import uuid
from datetime import datetime, timedelta

import pytest

from app.core.db import SessionLocal
from app.models.activity import ActivitySession, ActivityType
from app.models.metric import MasteryState, MetricAggregate
from app.models.microconcept import MicroConcept, MicroConceptPrerequisite
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


def test_generate_recommendations_prerequisites_r05(db_session, context):
    """
    Test R05: at-risk practiced concept with prerequisites generates prerequisite recommendation(s)
    """
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    mc_target = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Target", description="..."
    )
    mc_prereq_weak = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Prereq Weak", description="..."
    )
    mc_prereq_strong = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Prereq Strong", description="..."
    )
    db_session.add_all([mc_target, mc_prereq_weak, mc_prereq_strong])
    db_session.flush()

    db_session.add_all(
        [
            MicroConceptPrerequisite(
                microconcept_id=mc_target.id, prerequisite_microconcept_id=mc_prereq_weak.id
            ),
            MicroConceptPrerequisite(
                microconcept_id=mc_target.id, prerequisite_microconcept_id=mc_prereq_strong.id
            ),
        ]
    )

    now = datetime.now()
    db_session.add_all(
        [
            MasteryState(
                student_id=student.id,
                microconcept_id=mc_target.id,
                mastery_score=0.2,
                status="at_risk",
                last_practice_at=now,
                updated_at=now,
            ),
            MasteryState(
                student_id=student.id,
                microconcept_id=mc_prereq_weak.id,
                mastery_score=0.3,
                status="at_risk",
                last_practice_at=None,
                updated_at=now,
            ),
            MasteryState(
                student_id=student.id,
                microconcept_id=mc_prereq_strong.id,
                mastery_score=0.9,
                status="dominant",
                last_practice_at=now,
                updated_at=now,
            ),
        ]
    )
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )

    r05s = [r for r in recs if r.rule_id == "R05"]
    assert len(r05s) == 1
    assert r05s[0].microconcept_id == mc_prereq_weak.id
    assert any(ev.key == "target_microconcept_id" for ev in r05s[0].evidence)


def test_generate_recommendations_prerequisites_r05_requires_practice(db_session, context):
    """R05 should not fire for default at-risk concepts with no practice yet."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    mc_target = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Target", description="..."
    )
    mc_prereq = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Prereq", description="..."
    )
    db_session.add_all([mc_target, mc_prereq])
    db_session.flush()

    db_session.add(
        MicroConceptPrerequisite(
            microconcept_id=mc_target.id, prerequisite_microconcept_id=mc_prereq.id
        )
    )

    now = datetime.now()
    db_session.add_all(
        [
            MasteryState(
                student_id=student.id,
                microconcept_id=mc_target.id,
                mastery_score=0.0,
                status="at_risk",
                last_practice_at=None,
                updated_at=now,
            ),
            MasteryState(
                student_id=student.id,
                microconcept_id=mc_prereq.id,
                mastery_score=0.0,
                status="at_risk",
                last_practice_at=None,
                updated_at=now,
            ),
        ]
    )
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    assert all(r.rule_id != "R05" for r in recs)


def test_generate_recommendations_r02_in_progress_consolidate(db_session, context):
    """Test R02: in-progress practiced microconcept generates consolidation recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    mc = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Concept In Progress", description="..."
    )
    db_session.add(mc)
    db_session.flush()

    now = datetime.utcnow()
    db_session.add(
        MasteryState(
            student_id=student.id,
            microconcept_id=mc.id,
            mastery_score=0.6,
            status="in_progress",
            last_practice_at=now,
            recommended_next_review_at=now + timedelta(days=7),
            updated_at=now,
        )
    )
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r02 = next((r for r in recs if r.rule_id == "R02"), None)
    assert r02 is not None
    assert r02.microconcept_id == mc.id
    assert any(ev.key == "mastery_score" for ev in r02.evidence)


def test_generate_recommendations_r03_spaced_review_due(db_session, context):
    """Test R03: dominant microconcept with due review generates a spaced review recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    mc = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Concept Dominant", description="..."
    )
    db_session.add(mc)
    db_session.flush()

    now = datetime.utcnow()
    db_session.add(
        MasteryState(
            student_id=student.id,
            microconcept_id=mc.id,
            mastery_score=0.95,
            status="dominant",
            last_practice_at=now - timedelta(days=30),
            recommended_next_review_at=now - timedelta(days=1),
            updated_at=now,
        )
    )
    db_session.commit()

    recs1 = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r03 = next((r for r in recs1 if r.rule_id == "R03"), None)
    assert r03 is not None
    assert r03.microconcept_id is None
    assert any(ev.key == "due_review_count" for ev in r03.evidence)

    recs2 = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    assert any(r.rule_id == "R03" for r in recs2)
    pending = (
        db_session.query(RecommendationInstance)
        .filter(
            RecommendationInstance.student_id == student.id, RecommendationInstance.rule_id == "R03"
        )
        .all()
    )
    assert len(pending) == 1


def test_generate_recommendations_r12_limit_hints(db_session, context):
    """Test R12: high hint rate generates 'limit hints' recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    agg = MetricAggregate(
        student_id=student.id,
        scope_type="subject",
        scope_id=subject.id,
        accuracy=0.7,
        first_attempt_accuracy=0.55,
        median_response_time_ms=8000,
        attempts_per_item_avg=1.2,
        hint_rate=0.6,
        window_start=datetime.now(),
        window_end=datetime.now(),
        computed_at=datetime.now(),
    )
    db_session.add(agg)
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r12 = next((r for r in recs if r.rule_id == "R12"), None)
    assert r12 is not None
    assert any(ev.key == "hint_rate" for ev in r12.evidence)


def test_generate_recommendations_r16_change_activity_type(db_session, context):
    """Test R16: repeated quiz sessions trigger a change-activity recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)
        db_session.flush()

    now = datetime.utcnow()
    db_session.add_all(
        [
            ActivitySession(
                student_id=student.id,
                activity_type_id=quiz_type.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                started_at=now - timedelta(days=1),
                ended_at=now - timedelta(days=1) + timedelta(minutes=5),
                status="completed",
                device_type="web",
            ),
            ActivitySession(
                student_id=student.id,
                activity_type_id=quiz_type.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                started_at=now - timedelta(days=2),
                ended_at=now - timedelta(days=2) + timedelta(minutes=5),
                status="completed",
                device_type="web",
            ),
            ActivitySession(
                student_id=student.id,
                activity_type_id=quiz_type.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                started_at=now - timedelta(days=3),
                ended_at=now - timedelta(days=3) + timedelta(minutes=5),
                status="completed",
                device_type="web",
            ),
        ]
    )

    agg = MetricAggregate(
        student_id=student.id,
        scope_type="subject",
        scope_id=subject.id,
        accuracy=0.6,
        first_attempt_accuracy=0.45,
        median_response_time_ms=25000,
        attempts_per_item_avg=1.8,
        hint_rate=0.2,
        window_start=datetime.now(),
        window_end=datetime.now(),
        computed_at=datetime.now(),
    )
    db_session.add(agg)
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r16 = next((r for r in recs if r.rule_id == "R16"), None)
    assert r16 is not None
    assert any(ev.key == "dominant_activity_type" for ev in r16.evidence)


def test_generate_recommendations_r17_examples_for_weak_microconcept(db_session, context):
    """Test R17: at-risk practiced microconcept generates 'add examples' recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    mc = MicroConcept(
        subject_id=subject.id, term_id=term.id, name="Needs Examples", description="..."
    )
    db_session.add(mc)
    db_session.flush()

    now = datetime.utcnow()
    db_session.add(
        MasteryState(
            student_id=student.id,
            microconcept_id=mc.id,
            mastery_score=0.25,
            status="at_risk",
            last_practice_at=now,
            updated_at=now,
        )
    )
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r17 = next((r for r in recs if r.rule_id == "R17"), None)
    assert r17 is not None
    assert r17.microconcept_id == mc.id
    assert any(ev.key == "mastery_score" for ev in r17.evidence)


def test_generate_recommendations_r23_breaks_on_abandon(db_session, context):
    """Test R23: abandonment triggers break recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)
        db_session.flush()

    now = datetime.utcnow()
    db_session.add_all(
        [
            ActivitySession(
                student_id=student.id,
                activity_type_id=quiz_type.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                started_at=now - timedelta(days=1),
                ended_at=None,
                status="abandoned",
                device_type="web",
            ),
            ActivitySession(
                student_id=student.id,
                activity_type_id=quiz_type.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                started_at=now - timedelta(days=2),
                ended_at=None,
                status="abandoned",
                device_type="web",
            ),
        ]
    )

    agg = MetricAggregate(
        student_id=student.id,
        scope_type="subject",
        scope_id=subject.id,
        accuracy=0.7,
        first_attempt_accuracy=0.6,
        median_response_time_ms=9000,
        attempts_per_item_avg=1.4,
        hint_rate=0.1,
        abandon_rate=0.3,
        window_start=datetime.now(),
        window_end=datetime.now(),
        computed_at=datetime.now(),
    )
    db_session.add(agg)
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r23 = next((r for r in recs if r.rule_id == "R23"), None)
    assert r23 is not None
    assert any(ev.key == "abandon_rate" for ev in r23.evidence)


def test_generate_recommendations_r26_automation_when_slow_but_correct(db_session, context):
    """Test R26: high accuracy + slow responses triggers automation recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    agg = MetricAggregate(
        student_id=student.id,
        scope_type="subject",
        scope_id=subject.id,
        accuracy=0.9,
        first_attempt_accuracy=0.85,
        median_response_time_ms=20000,
        attempts_per_item_avg=1.1,
        hint_rate=0.1,
        abandon_rate=0.0,
        window_start=datetime.now(),
        window_end=datetime.now(),
        computed_at=datetime.now(),
    )
    db_session.add(agg)
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r26 = next((r for r in recs if r.rule_id == "R26"), None)
    assert r26 is not None
    assert any(ev.key == "median_response_time_ms" for ev in r26.evidence)


def test_generate_recommendations_r30_alternate_intensive_light_days(db_session, context):
    """Test R30: many active days triggers alternation recommendation."""
    student = context["student"]
    subject = context["subject"]
    term = context["term"]

    quiz_type = db_session.query(ActivityType).filter_by(code="QUIZ").first()
    if not quiz_type:
        quiz_type = ActivityType(code="QUIZ", name="Quiz", active=True)
        db_session.add(quiz_type)
        db_session.flush()

    now = datetime.utcnow()
    sessions = []
    for offset in range(1, 7):
        start = now - timedelta(days=offset)
        sessions.append(
            ActivitySession(
                student_id=student.id,
                activity_type_id=quiz_type.id,
                subject_id=subject.id,
                term_id=term.id,
                topic_id=None,
                started_at=start,
                ended_at=start + timedelta(minutes=5),
                status="completed",
                device_type="web",
            )
        )
    start = now - timedelta(days=1, hours=1)
    sessions.append(
        ActivitySession(
            student_id=student.id,
            activity_type_id=quiz_type.id,
            subject_id=subject.id,
            term_id=term.id,
            topic_id=None,
            started_at=start,
            ended_at=start + timedelta(minutes=5),
            status="completed",
            device_type="web",
        )
    )
    start = now - timedelta(days=2, hours=1)
    sessions.append(
        ActivitySession(
            student_id=student.id,
            activity_type_id=quiz_type.id,
            subject_id=subject.id,
            term_id=term.id,
            topic_id=None,
            started_at=start,
            ended_at=start + timedelta(minutes=5),
            status="completed",
            device_type="web",
        )
    )
    db_session.add_all(sessions)

    agg = MetricAggregate(
        student_id=student.id,
        scope_type="subject",
        scope_id=subject.id,
        accuracy=0.75,
        first_attempt_accuracy=0.7,
        median_response_time_ms=10000,
        attempts_per_item_avg=1.3,
        hint_rate=0.1,
        abandon_rate=0.0,
        window_start=datetime.now(),
        window_end=datetime.now(),
        computed_at=datetime.now(),
    )
    db_session.add(agg)
    db_session.commit()

    recs = recommendation_service.generate_recommendations(
        db_session, student.id, subject.id, term.id
    )
    r30 = next((r for r in recs if r.rule_id == "R30"), None)
    assert r30 is not None
    assert any(ev.key == "days_with_sessions_7d" for ev in r30.evidence)


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
