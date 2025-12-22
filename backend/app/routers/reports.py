import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_active_user, get_current_role_name, get_current_tutor
from app.models.activity import ActivitySession
from app.models.report import TutorReport
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import Term
from app.models.user import User
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
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    tutor_id: uuid.UUID | None = None,
    generate_recommendations: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")

    tutor = get_current_tutor(db=db, current_user=current_user)
    if tutor_id and tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Tutor mismatch")
    tutor_id = tutor.id

    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if not db.get(Term, term_id):
        raise HTTPException(status_code=404, detail="Term not found")
    if subject.tutor_id and subject.tutor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    student = db.get(Student, student_id)
    if student and student.subject_id and student.subject_id != subject_id:
        raise HTTPException(status_code=403, detail="Not allowed")

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
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    tutor_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")

    tutor = get_current_tutor(db=db, current_user=current_user)
    if tutor_id and tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Tutor mismatch")
    tutor_id = tutor.id

    subject = db.get(Subject, subject_id)
    if subject and subject.tutor_id and subject.tutor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    student = db.get(Student, student_id)
    if student and student.subject_id and student.subject_id != subject_id:
        raise HTTPException(status_code=403, detail="Not allowed")

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

    latest_feedback_at = (
        db.query(func.max(ActivitySession.feedback_submitted_at))
        .filter(
            ActivitySession.student_id == student_id,
            ActivitySession.subject_id == subject_id,
            ActivitySession.term_id == term_id,
            ActivitySession.feedback_submitted_at.is_not(None),
        )
        .scalar()
    )

    needs_regen = False
    if latest_feedback_at and report and report.generated_at:
        needs_regen = latest_feedback_at > report.generated_at
    elif latest_feedback_at and not report:
        needs_regen = True

    if needs_regen or report is None:
        try:
            report = report_service.generate_student_report(
                db,
                tutor_id=tutor_id,
                student_id=student_id,
                subject_id=subject_id,
                term_id=term_id,
                generate_recommendations=True,
            )
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Database error generating report while refreshing feedback."
                    "If you just updated the repo, run migrations: `alembic upgrade head`."
                ),
            ) from exc

    if not report:
        raise HTTPException(status_code=404, detail="No report found")
    return report


@router.get("", response_model=list[TutorReportListItemResponse])
def list_reports(
    tutor_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    term_id: uuid.UUID | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")

    tutor = get_current_tutor(db=db, current_user=current_user)
    if tutor_id and tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Tutor mismatch")
    tutor_id = tutor.id

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
    tutor_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name != "tutor":
        raise HTTPException(status_code=403, detail="Role not allowed")

    tutor = get_current_tutor(db=db, current_user=current_user)
    if tutor_id and tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Tutor mismatch")
    tutor_id = tutor.id

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
