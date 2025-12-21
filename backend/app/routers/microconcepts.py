import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user, require_roles
from app.models.activity import LearningEvent
from app.models.content import ContentUpload
from app.models.item import Item
from app.models.microconcept import MicroConcept, MicroConceptPrerequisite
from app.models.subject import Subject
from app.models.user import User
from app.schemas.microconcept import (
    MicroConceptCreate,
    MicroConceptPrerequisiteLinkCreate,
    MicroConceptPrerequisiteResponse,
    MicroConceptResponse,
    MicroConceptUpdate,
)

router = APIRouter(prefix="/microconcepts", tags=["microconcepts"])


def _require_tutor_owns_subject(db: Session, current_user: User, subject_id: uuid.UUID) -> Subject:
    require_roles(db, current_user, {"tutor"})
    subject = db.get(Subject, subject_id)
    if not subject or subject.tutor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return subject


def _require_tutor_owns_microconcept(
    db: Session, current_user: User, microconcept_id: uuid.UUID
) -> MicroConcept:
    require_roles(db, current_user, {"tutor"})
    microconcept = db.get(MicroConcept, microconcept_id)
    if not microconcept:
        raise HTTPException(status_code=404, detail="Microconcept not found")
    _require_tutor_owns_subject(
        db=db, current_user=current_user, subject_id=microconcept.subject_id
    )
    return microconcept


def _would_create_cycle(
    db: Session, microconcept_id: uuid.UUID, prerequisite_id: uuid.UUID
) -> bool:
    # If there's already a path prerequisite_id -> ... -> microconcept_id, adding
    # microconcept_id -> prerequisite_id would create a cycle.
    visited: set[uuid.UUID] = set()
    frontier: list[uuid.UUID] = [prerequisite_id]

    while frontier:
        current = frontier.pop()
        if current == microconcept_id:
            return True
        if current in visited:
            continue
        visited.add(current)

        next_nodes = (
            db.query(MicroConceptPrerequisite.prerequisite_microconcept_id)
            .filter(MicroConceptPrerequisite.microconcept_id == current)
            .all()
        )
        frontier.extend([row[0] for row in next_nodes if row[0] not in visited])

    return False


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


@router.get(
    "/{microconcept_id}/prerequisites",
    response_model=list[MicroConceptPrerequisiteResponse],
)
def list_microconcept_prerequisites(
    microconcept_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List prerequisite relations for a microconcept (tutor-only).
    """
    _require_tutor_owns_microconcept(
        db=db, current_user=current_user, microconcept_id=microconcept_id
    )
    return (
        db.query(MicroConceptPrerequisite)
        .filter(MicroConceptPrerequisite.microconcept_id == microconcept_id)
        .order_by(MicroConceptPrerequisite.created_at.asc())
        .all()
    )


@router.post(
    "/{microconcept_id}/prerequisites",
    response_model=MicroConceptPrerequisiteResponse,
)
def add_microconcept_prerequisite(
    microconcept_id: uuid.UUID,
    payload: MicroConceptPrerequisiteLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a prerequisite relation (tutor-only).

    Validations:
    - no self prerequisite
    - prerequisite must belong to same subject + term
    - no duplicates
    - no cycles
    """
    microconcept = _require_tutor_owns_microconcept(
        db=db, current_user=current_user, microconcept_id=microconcept_id
    )

    prerequisite_id = payload.prerequisite_microconcept_id
    if prerequisite_id == microconcept_id:
        raise HTTPException(status_code=400, detail="Prerequisite cannot be itself")

    prerequisite = _require_tutor_owns_microconcept(
        db=db, current_user=current_user, microconcept_id=prerequisite_id
    )

    if (
        prerequisite.subject_id != microconcept.subject_id
        or prerequisite.term_id != microconcept.term_id
    ):
        raise HTTPException(status_code=400, detail="Prerequisite must match subject/term")

    existing = (
        db.query(MicroConceptPrerequisite)
        .filter(
            MicroConceptPrerequisite.microconcept_id == microconcept_id,
            MicroConceptPrerequisite.prerequisite_microconcept_id == prerequisite_id,
        )
        .first()
    )
    if existing:
        return existing

    if _would_create_cycle(db=db, microconcept_id=microconcept_id, prerequisite_id=prerequisite_id):
        raise HTTPException(status_code=400, detail="Prerequisite would create a cycle")

    link = MicroConceptPrerequisite(
        id=uuid.uuid4(),
        microconcept_id=microconcept_id,
        prerequisite_microconcept_id=prerequisite_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.delete("/{microconcept_id}/prerequisites/{prerequisite_microconcept_id}")
def remove_microconcept_prerequisite(
    microconcept_id: uuid.UUID,
    prerequisite_microconcept_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Remove a prerequisite relation (tutor-only).
    """
    _require_tutor_owns_microconcept(
        db=db, current_user=current_user, microconcept_id=microconcept_id
    )
    deleted = (
        db.query(MicroConceptPrerequisite)
        .filter(
            MicroConceptPrerequisite.microconcept_id == microconcept_id,
            MicroConceptPrerequisite.prerequisite_microconcept_id == prerequisite_microconcept_id,
        )
        .delete()
    )
    db.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="Prerequisite relation not found")

    return {"status": "success"}


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
