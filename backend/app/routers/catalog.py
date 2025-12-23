import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, or_
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_active_user, get_current_tutor
from app.models.activity import ActivitySession, ActivitySessionItem, LearningEvent
from app.models.content import ContentUpload
from app.models.grade import RealGrade
from app.models.microconcept import MicroConcept, MicroConceptPrerequisite
from app.models.recommendation import RecommendationInstance
from app.models.report import TutorReport
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.topic import Topic
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.catalog import (
    StudentSubjectUpdate,
    StudentSummary,
    SubjectCreate,
    SubjectSummary,
    SubjectUpdate,
    TermSummary,
    TopicSummary,
)

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
    query = (
        db.query(Term)
        .options(selectinload(Term.academic_year))
        .outerjoin(Term.academic_year)
    )
    if active is True:
        query = query.filter(Term.status == "active")

    query = query.filter(
        or_(
            AcademicYear.name.is_(None),
            AcademicYear.name.op("~")(r"^\d{4}-\d{4}$"),
        )
    )

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


@router.post("/subjects", response_model=SubjectSummary, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    subject = Subject(
        id=uuid.uuid4(),
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        tutor_id=current_tutor.user_id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.put("/subjects/{subject_id}", response_model=SubjectSummary)
def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    subject = db.get(Subject, subject_id)
    if not subject or subject.tutor_id != current_tutor.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignatura no encontrada")

    if payload.name is None and payload.description is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nada que actualizar")

    if payload.name:
        subject.name = payload.name.strip()
    if payload.description is not None:
        subject.description = payload.description.strip() or None

    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
    force: bool = False,
):
    subject = db.get(Subject, subject_id)
    if not subject or subject.tutor_id != current_tutor.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignatura no encontrada")

    if force:
        _purge_subject_dependencies(db, subject.id)
    else:
        dependency_models = (
            MicroConcept,
            ContentUpload,
            Student,
            ActivitySession,
            RealGrade,
            RecommendationInstance,
            TutorReport,
        )
        has_dependencies = any(
            db.query(model)
            .filter(getattr(model, "subject_id") == subject.id)
            .first()
            for model in dependency_models
        )

        if has_dependencies:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar mientras existan datos asociados",
            )

    db.delete(subject)
    db.commit()


@router.patch("/students/{student_id}", response_model=StudentSummary)
def assign_student_subject(
    student_id: uuid.UUID,
    payload: StudentSubjectUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    subject = db.get(Subject, payload.subject_id)
    if not subject or subject.tutor_id != current_tutor.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignatura no encontrada")

    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    student.subject_id = subject.id
    db.add(student)
    db.commit()
    db.refresh(student)

    user = db.get(User, student.user_id) if student.user_id else None
    return StudentSummary(
        id=student.id,
        user_id=student.user_id,
        subject_id=student.subject_id,
        enrollment_date=student.enrollment_date,
        email=user.email if user else None,
        full_name=user.full_name if user else None,
    )


def _purge_subject_dependencies(db: Session, subject_id: uuid.UUID) -> None:
    session_ids = [row.id for row in db.query(ActivitySession.id).filter(ActivitySession.subject_id == subject_id).all()]
    if session_ids:
        db.execute(delete(ActivitySessionItem).where(ActivitySessionItem.session_id.in_(session_ids)))
    db.execute(delete(LearningEvent).where(LearningEvent.subject_id == subject_id))
    db.execute(delete(ActivitySession).where(ActivitySession.subject_id == subject_id))
    db.execute(delete(ContentUpload).where(ContentUpload.subject_id == subject_id))
    db.execute(delete(RealGrade).where(RealGrade.subject_id == subject_id))
    db.execute(delete(TutorReport).where(TutorReport.subject_id == subject_id))
    micro_ids = [row.id for row in db.query(MicroConcept.id).filter(MicroConcept.subject_id == subject_id).all()]
    if micro_ids:
        db.execute(
            delete(MicroConceptPrerequisite).where(
                or_(
                    MicroConceptPrerequisite.microconcept_id.in_(micro_ids),
                    MicroConceptPrerequisite.prerequisite_microconcept_id.in_(micro_ids),
                )
            )
        )
    db.execute(delete(MicroConcept).where(MicroConcept.subject_id == subject_id))
    db.execute(delete(RecommendationInstance).where(RecommendationInstance.subject_id == subject_id))
    db.execute(delete(Topic).where(Topic.subject_id == subject_id))
    db.query(Student).filter(Student.subject_id == subject_id).update({Student.subject_id: None}, synchronize_session="fetch")


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
