import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.models.report import TutorReport
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term
from app.models.tutor import Tutor
from app.schemas.report import TutorReportListItemResponse, TutorReportResponse
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/students/{student_id}/generate",
    response_model=TutorReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_student_report(
    student_id: uuid.UUID,
    tutor_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    generate_recommendations: bool = True,
    db: Session = Depends(get_db),
):
    if not db.get(Tutor, tutor_id):
        raise HTTPException(status_code=404, detail="Tutor not found")
    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    if not db.get(Subject, subject_id):
        raise HTTPException(status_code=404, detail="Subject not found")
    if not db.get(Term, term_id):
        raise HTTPException(status_code=404, detail="Term not found")

    try:
        report = report_service.generate_student_report(
            db,
            tutor_id=tutor_id,
            student_id=student_id,
            subject_id=subject_id,
            term_id=term_id,
            generate_recommendations=generate_recommendations,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Database error generating report. "
                "If you just updated the repo, run migrations: `alembic upgrade head`."
            ),
        ) from exc

    return report


@router.get("/students/{student_id}/latest", response_model=TutorReportResponse)
def get_latest_student_report(
    student_id: uuid.UUID,
    tutor_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    try:
        report = report_service.get_latest_report(
            db,
            tutor_id=tutor_id,
            student_id=student_id,
            subject_id=subject_id,
            term_id=term_id,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Database error reading reports. "
                "If you just updated the repo, run migrations: `alembic upgrade head`."
            ),
        ) from exc

    if not report:
        raise HTTPException(status_code=404, detail="No report found")
    return report


@router.get("", response_model=list[TutorReportListItemResponse])
def list_reports(
    tutor_id: uuid.UUID,
    student_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    term_id: uuid.UUID | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(TutorReport).filter(TutorReport.tutor_id == tutor_id)
    if student_id:
        query = query.filter(TutorReport.student_id == student_id)
    if subject_id:
        query = query.filter(TutorReport.subject_id == subject_id)
    if term_id:
        query = query.filter(TutorReport.term_id == term_id)

    try:
        return query.order_by(TutorReport.generated_at.desc()).limit(limit).all()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Database error listing reports.",
        ) from exc


@router.get("/{report_id}", response_model=TutorReportResponse)
def get_report(
    report_id: uuid.UUID,
    tutor_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    try:
        report = (
            db.query(TutorReport)
            .options(selectinload(TutorReport.sections))
            .filter(TutorReport.id == report_id, TutorReport.tutor_id == tutor_id)
            .first()
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Database error reading report.",
        ) from exc

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
