import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.microconcept import MicroConcept
from app.schemas.microconcept import MicroConceptCreate, MicroConceptResponse

router = APIRouter(prefix="/microconcepts", tags=["microconcepts"])


@router.get("/subjects/{subject_id}", response_model=list[MicroConceptResponse])
def list_microconcepts(
    subject_id: uuid.UUID,
    term_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    """
    List all microconcepts for a subject (optionally filtered by term).
    """
    query = db.query(MicroConcept).filter(
        MicroConcept.subject_id == subject_id,
        MicroConcept.active == True,  # noqa: E712
    )

    if term_id:
        query = query.filter(MicroConcept.term_id == term_id)

    microconcepts = query.order_by(MicroConcept.name).all()

    return microconcepts


@router.post("", response_model=MicroConceptResponse)
def create_microconcept(microconcept_data: MicroConceptCreate, db: Session = Depends(get_db)):
    """
    Create a new microconcept (tutor/admin only in production).
    """
    microconcept = MicroConcept(
        id=uuid.uuid4(),
        subject_id=microconcept_data.subject_id,
        term_id=microconcept_data.term_id,
        topic_id=microconcept_data.topic_id,
        code=microconcept_data.code,
        name=microconcept_data.name,
        description=microconcept_data.description,
        active=microconcept_data.active,
    )

    db.add(microconcept)
    db.commit()
    db.refresh(microconcept)

    return microconcept


@router.get("/{microconcept_id}", response_model=MicroConceptResponse)
def get_microconcept(microconcept_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a microconcept by ID.
    """
    microconcept = db.query(MicroConcept).filter_by(id=microconcept_id).first()
    if not microconcept:
        raise HTTPException(status_code=404, detail="Microconcept not found")

    return microconcept
