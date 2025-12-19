import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user, require_roles
from app.models.activity import LearningEvent
from app.models.content import ContentUpload
from app.models.item import Item
from app.models.microconcept import MicroConcept
from app.models.subject import Subject
from app.models.user import User
from app.schemas.microconcept import MicroConceptCreate, MicroConceptResponse, MicroConceptUpdate

router = APIRouter(prefix="/microconcepts", tags=["microconcepts"])


def _require_tutor_owns_subject(db: Session, current_user: User, subject_id: uuid.UUID) -> Subject:
    require_roles(db, current_user, {"tutor"})
    subject = db.get(Subject, subject_id)
    if not subject or subject.tutor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return subject


@router.get("/subjects/{subject_id}", response_model=list[MicroConceptResponse])
def list_microconcepts(
    subject_id: uuid.UUID,
    term_id: uuid.UUID | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all microconcepts for a subject (optionally filtered by term).

    Tutor-only: the tutor must own the subject.
    """
    _require_tutor_owns_subject(db=db, current_user=current_user, subject_id=subject_id)

    query = db.query(MicroConcept).filter(MicroConcept.subject_id == subject_id)

    if term_id:
        query = query.filter(MicroConcept.term_id == term_id)

    if active is not None:
        query = query.filter(MicroConcept.active == active)

    microconcepts = query.order_by(MicroConcept.name).all()

    return microconcepts


@router.post("", response_model=MicroConceptResponse)
def create_microconcept(
    microconcept_data: MicroConceptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new microconcept (tutor-only).
    """
    _require_tutor_owns_subject(
        db=db, current_user=current_user, subject_id=microconcept_data.subject_id
    )

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
def get_microconcept(
    microconcept_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a microconcept by ID.
    """
    microconcept = db.query(MicroConcept).filter_by(id=microconcept_id).first()
    if not microconcept:
        raise HTTPException(status_code=404, detail="Microconcept not found")

    _require_tutor_owns_subject(
        db=db, current_user=current_user, subject_id=microconcept.subject_id
    )

    return microconcept


@router.patch("/{microconcept_id}", response_model=MicroConceptResponse)
def update_microconcept(
    microconcept_id: uuid.UUID,
    microconcept_update: MicroConceptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Patch a microconcept (tutor-only).
    """
    microconcept = db.query(MicroConcept).filter_by(id=microconcept_id).first()
    if not microconcept:
        raise HTTPException(status_code=404, detail="Microconcept not found")

    _require_tutor_owns_subject(
        db=db, current_user=current_user, subject_id=microconcept.subject_id
    )

    updates = microconcept_update.model_dump(exclude_unset=True)
    for field_name, value in updates.items():
        setattr(microconcept, field_name, value)

    db.add(microconcept)
    db.commit()
    db.refresh(microconcept)

    return microconcept


@router.post("/bootstrap")
def bootstrap_microconcepts_for_scope(
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Dev-only helper: ensures the subject/term has at least one microconcept ("General"),
    and aligns items + learning_events in that scope to reference it.

    This unblocks mastery calculations when the dataset has practice sessions but no
    microconcept taxonomy yet.
    """
    _require_tutor_owns_subject(db=db, current_user=current_user, subject_id=subject_id)

    microconcept = (
        db.query(MicroConcept)
        .filter(
            MicroConcept.subject_id == subject_id,
            MicroConcept.term_id == term_id,
            MicroConcept.active == True,  # noqa: E712
        )
        .order_by(MicroConcept.created_at.asc())
        .first()
    )

    created = False
    if not microconcept:
        microconcept = MicroConcept(
            id=uuid.uuid4(),
            subject_id=subject_id,
            term_id=term_id,
            topic_id=None,
            code=None,
            name="General",
            description="Microconcepto genérico (bootstrap dev)",
            active=True,
        )
        db.add(microconcept)
        db.commit()
        db.refresh(microconcept)
        created = True

    items = (
        db.query(Item)
        .join(ContentUpload, Item.content_upload_id == ContentUpload.id)
        .filter(ContentUpload.subject_id == subject_id, ContentUpload.term_id == term_id)
        .all()
    )
    updated_items = 0
    for item in items:
        if item.microconcept_id != microconcept.id:
            item.microconcept_id = microconcept.id
            updated_items += 1

    updated_events = (
        db.query(LearningEvent)
        .filter(LearningEvent.subject_id == subject_id, LearningEvent.term_id == term_id)
        .update({LearningEvent.microconcept_id: microconcept.id})
    )

    db.commit()

    return {
        "status": "success",
        "microconcept_id": str(microconcept.id),
        "created": created,
        "updated_items": updated_items,
        "updated_events": int(updated_events or 0),
    }
