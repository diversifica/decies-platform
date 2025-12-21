import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term
from app.models.topic import Topic
from app.models.user import User
from app.schemas.catalog import StudentSummary, SubjectSummary, TermSummary, TopicSummary

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _get_role_name(db: Session, user: User) -> str | None:
    if not user.role_id:
        return None
    role = db.get(Role, user.role_id)
    return role.name if role else None


@router.get("/terms", response_model=list[TermSummary])
def list_terms(
    active: bool | None = True,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    query = db.query(Term)
    if active is True:
        query = query.filter(Term.status == "active")
    return query.order_by(Term.code).all()


@router.get("/subjects", response_model=list[SubjectSummary])
def list_subjects(
    mine: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Subject)
    if mine:
        query = query.filter(Subject.tutor_id == current_user.id)
    return query.order_by(Subject.name).all()


@router.get("/students", response_model=list[StudentSummary])
def list_students(
    mine: bool = True,
    subject_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = (_get_role_name(db, current_user) or "").casefold()

    if role_name == "student":
        student = (
            db.query(Student)
            .filter((Student.user_id == current_user.id) | (Student.id == current_user.id))
            .first()
        )
        if not student:
            return []
        return [
            StudentSummary(
                id=student.id,
                user_id=student.user_id,
                subject_id=student.subject_id,
                enrollment_date=student.enrollment_date,
                email=current_user.email,
                full_name=current_user.full_name,
            )
        ]

    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")

    subjects_query = db.query(Subject).filter(Subject.tutor_id == current_user.id)
    if subject_id:
        subjects_query = subjects_query.filter(Subject.id == subject_id)
    subject_ids = [row.id for row in subjects_query.all()]

    if not subject_ids and mine:
        return []

    student_query = db.query(Student)
    if mine and subject_ids:
        student_query = student_query.filter(Student.subject_id.in_(subject_ids))
    elif subject_id:
        student_query = student_query.filter(Student.subject_id == subject_id)

    students = student_query.order_by(Student.enrollment_date.desc().nullslast()).all()

    users = {}
    user_ids = [s.user_id for s in students if s.user_id]
    if user_ids:
        for user in db.query(User).filter(User.id.in_(user_ids)).all():
            users[user.id] = user

    results: list[StudentSummary] = []
    for student in students:
        user = users.get(student.user_id) if student.user_id else None
        results.append(
            StudentSummary(
                id=student.id,
                user_id=student.user_id,
                subject_id=student.subject_id,
                enrollment_date=student.enrollment_date,
                email=user.email if user else None,
                full_name=user.full_name if user else None,
            )
        )
    return results


@router.get("/topics", response_model=list[TopicSummary])
def list_topics(
    mine: bool = True,
    subject_id: uuid.UUID | None = None,
    term_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = (_get_role_name(db, current_user) or "").casefold()

    query = db.query(Topic)

    if role_name == "student":
        student = (
            db.query(Student)
            .filter((Student.user_id == current_user.id) | (Student.id == current_user.id))
            .first()
        )
        if not student or not student.subject_id:
            return []
        query = query.filter(Topic.subject_id == student.subject_id)
    elif role_name == "tutor":
        if mine:
            query = query.join(Subject, Topic.subject_id == Subject.id).filter(
                Subject.tutor_id == current_user.id
            )
    else:
        raise HTTPException(status_code=403, detail="Role not allowed")

    if subject_id:
        if role_name == "tutor" and mine:
            subject = db.get(Subject, subject_id)
            if subject and subject.tutor_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not allowed")
        query = query.filter(Topic.subject_id == subject_id)

    if term_id:
        query = query.filter(Topic.term_id == term_id)

    return query.order_by(Topic.order_index, Topic.name).all()
