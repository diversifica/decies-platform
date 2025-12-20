import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_tutor
from app.models.grade import AssessmentScopeTag, RealGrade
from app.models.microconcept import MicroConcept
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term
from app.models.topic import Topic
from app.models.tutor import Tutor
from app.schemas.grade import (
    AssessmentScopeTagCreate,
    AssessmentScopeTagResponse,
    RealGradeCreate,
    RealGradeResponse,
    RealGradeUpdate,
)

router = APIRouter(prefix="/grades", tags=["grades"])


def _require_subject_owned(db: Session, tutor: Tutor, subject_id: uuid.UUID) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.tutor_id and subject.tutor_id != tutor.user_id:
        raise HTTPException(status_code=403, detail="Subject not owned by tutor")
    return subject


def _require_student_subject(db: Session, student_id: uuid.UUID, subject_id: uuid.UUID) -> Student:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.subject_id and student.subject_id != subject_id:
        raise HTTPException(status_code=403, detail="Student not allowed for subject")
    return student


def _require_term(db: Session, term_id: uuid.UUID) -> Term:
    term = db.get(Term, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return term


def _validate_tag_payload(db: Session, grade: RealGrade, payload: AssessmentScopeTagCreate) -> None:
    if not payload.topic_id and not payload.microconcept_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one of topic_id or microconcept_id is required",
        )

    if payload.topic_id:
        topic = db.get(Topic, payload.topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        if topic.subject_id != grade.subject_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Topic subject does not match grade subject",
            )
        if topic.term_id and topic.term_id != grade.term_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Topic term does not match grade term",
            )

    if payload.microconcept_id:
        microconcept = db.get(MicroConcept, payload.microconcept_id)
        if not microconcept:
            raise HTTPException(status_code=404, detail="Microconcept not found")
        if microconcept.subject_id != grade.subject_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Microconcept subject does not match grade subject",
            )
        if microconcept.term_id and microconcept.term_id != grade.term_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Microconcept term does not match grade term",
            )


def _require_grade_owned(db: Session, tutor: Tutor, grade_id: uuid.UUID) -> RealGrade:
    grade = (
        db.query(RealGrade)
        .options(selectinload(RealGrade.scope_tags))
        .filter(RealGrade.id == grade_id)
        .first()
    )
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    if grade.created_by_tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    _require_subject_owned(db, tutor, grade.subject_id)
    return grade


@router.post("", response_model=RealGradeResponse, status_code=status.HTTP_201_CREATED)
def create_real_grade(
    payload: RealGradeCreate,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    _require_subject_owned(db, current_tutor, payload.subject_id)
    _require_student_subject(db, payload.student_id, payload.subject_id)
    _require_term(db, payload.term_id)

    grade = RealGrade(
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        term_id=payload.term_id,
        assessment_date=payload.assessment_date,
        grade_value=payload.grade_value,
        grading_scale=payload.grading_scale,
        notes=payload.notes,
        created_by_tutor_id=current_tutor.id,
    )
    db.add(grade)
    db.flush()

    for tag_payload in payload.scope_tags:
        _validate_tag_payload(db, grade, tag_payload)
        db.add(
            AssessmentScopeTag(
                real_grade_id=grade.id,
                topic_id=tag_payload.topic_id,
                microconcept_id=tag_payload.microconcept_id,
                weight=tag_payload.weight,
            )
        )

    db.commit()
    return _require_grade_owned(db, current_tutor, grade.id)


@router.get("", response_model=list[RealGradeResponse])
def list_real_grades(
    student_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    term_id: uuid.UUID | None = None,
    limit: int = 50,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    query = (
        db.query(RealGrade)
        .options(selectinload(RealGrade.scope_tags))
        .filter(RealGrade.created_by_tutor_id == current_tutor.id)
    )

    if student_id:
        query = query.filter(RealGrade.student_id == student_id)
    if subject_id:
        _require_subject_owned(db, current_tutor, subject_id)
        query = query.filter(RealGrade.subject_id == subject_id)
    if term_id:
        _require_term(db, term_id)
        query = query.filter(RealGrade.term_id == term_id)

    return query.order_by(RealGrade.assessment_date.desc()).limit(limit).all()


@router.get("/{grade_id}", response_model=RealGradeResponse)
def get_real_grade(
    grade_id: uuid.UUID,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    return _require_grade_owned(db, current_tutor, grade_id)


@router.patch("/{grade_id}", response_model=RealGradeResponse)
def update_real_grade(
    grade_id: uuid.UUID,
    payload: RealGradeUpdate,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    grade = _require_grade_owned(db, current_tutor, grade_id)

    if payload.assessment_date is not None:
        grade.assessment_date = payload.assessment_date
    if payload.grade_value is not None:
        grade.grade_value = payload.grade_value
    if payload.grading_scale is not None:
        grade.grading_scale = payload.grading_scale
    if payload.notes is not None:
        grade.notes = payload.notes

    db.add(grade)
    db.commit()
    return _require_grade_owned(db, current_tutor, grade_id)


@router.delete("/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_real_grade(
    grade_id: uuid.UUID,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    grade = _require_grade_owned(db, current_tutor, grade_id)
    db.delete(grade)
    db.commit()
    return None


@router.get("/{grade_id}/tags", response_model=list[AssessmentScopeTagResponse])
def list_grade_tags(
    grade_id: uuid.UUID,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    grade = _require_grade_owned(db, current_tutor, grade_id)
    return grade.scope_tags


@router.post(
    "/{grade_id}/tags",
    response_model=AssessmentScopeTagResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_grade_tag(
    grade_id: uuid.UUID,
    payload: AssessmentScopeTagCreate,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    grade = _require_grade_owned(db, current_tutor, grade_id)
    _validate_tag_payload(db, grade, payload)

    tag = AssessmentScopeTag(
        real_grade_id=grade.id,
        topic_id=payload.topic_id,
        microconcept_id=payload.microconcept_id,
        weight=payload.weight,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.patch("/{grade_id}/tags/{tag_id}", response_model=AssessmentScopeTagResponse)
def update_grade_tag(
    grade_id: uuid.UUID,
    tag_id: uuid.UUID,
    payload: AssessmentScopeTagCreate,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    grade = _require_grade_owned(db, current_tutor, grade_id)
    tag = db.query(AssessmentScopeTag).filter_by(id=tag_id, real_grade_id=grade.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    _validate_tag_payload(db, grade, payload)

    tag.topic_id = payload.topic_id
    tag.microconcept_id = payload.microconcept_id
    tag.weight = payload.weight
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{grade_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grade_tag(
    grade_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    grade = _require_grade_owned(db, current_tutor, grade_id)
    tag = db.query(AssessmentScopeTag).filter_by(id=tag_id, real_grade_id=grade.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return None
