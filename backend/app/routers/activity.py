import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.activity import (
    ActivitySession,
    ActivitySessionItem,
    ActivityType,
    LearningEvent,
)
from app.models.item import Item
from app.schemas.activity import (
    ActivitySessionCreate,
    ActivitySessionResponse,
    ActivityTypeResponse,
    LearningEventCreate,
    LearningEventResponse,
)
from app.services.metric_service import metric_service

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/activity-types", response_model=list[ActivityTypeResponse])
def list_activity_types(db: Session = Depends(get_db)):
    """
    List all activity types.
    """
    types = db.query(ActivityType).filter_by(active=True).all()
    return types


@router.post("/sessions", response_model=ActivitySessionResponse)
def create_session(session_data: ActivitySessionCreate, db: Session = Depends(get_db)):
    """
    Create a new activity session with randomly selected items.
    """
    # Get activity type
    activity_type = db.query(ActivityType).filter_by(id=session_data.activity_type_id).first()
    if not activity_type:
        raise HTTPException(status_code=404, detail="Activity type not found")

    # Create session
    session = ActivitySession(
        id=uuid.uuid4(),
        student_id=session_data.student_id,
        activity_type_id=session_data.activity_type_id,
        subject_id=session_data.subject_id,
        term_id=session_data.term_id,
        topic_id=session_data.topic_id,
        started_at=datetime.utcnow(),
        status="in_progress",
        device_type=session_data.device_type,
    )
    db.add(session)
    db.flush()

    # Select random items for this session
    # Items are linked to content_uploads, which are linked to subjects
    from app.models.content import ContentUpload

    items = (
        db.query(Item)
        .join(ContentUpload, Item.content_upload_id == ContentUpload.id)
        .filter(
            ContentUpload.subject_id == session_data.subject_id,
            ContentUpload.term_id == session_data.term_id,
        )
        .order_by(Item.id)  # Simple ordering, could be randomized
        .limit(session_data.item_count)
        .all()
    )

    if not items:
        raise HTTPException(status_code=404, detail="No items found for this subject/term")

    # Create session items
    for idx, item in enumerate(items):
        session_item = ActivitySessionItem(
            id=uuid.uuid4(),
            session_id=session.id,
            item_id=item.id,
            order_index=idx,
            presented_at=datetime.utcnow() if idx == 0 else None,
        )
        db.add(session_item)

    db.commit()
    db.refresh(session)

    return session


@router.get("/sessions/{session_id}", response_model=ActivitySessionResponse)
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get an activity session by ID.
    """
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post("/sessions/{session_id}/responses", response_model=LearningEventResponse)
def record_response(
    session_id: uuid.UUID, event_data: LearningEventCreate, db: Session = Depends(get_db)
):
    """
    Record a student response as a learning event.
    """
    # Verify session exists
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")

    # Get item to derive microconcept_id if not provided
    item = db.query(Item).filter_by(id=event_data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Create learning event
    event = LearningEvent(
        id=uuid.uuid4(),
        student_id=event_data.student_id,
        session_id=session_id,
        subject_id=event_data.subject_id,
        term_id=event_data.term_id,
        topic_id=event_data.topic_id,
        microconcept_id=event_data.microconcept_id or item.microconcept_id,
        activity_type_id=event_data.activity_type_id,
        item_id=event_data.item_id,
        timestamp_start=event_data.timestamp_start,
        timestamp_end=event_data.timestamp_end,
        duration_ms=event_data.duration_ms,
        attempt_number=event_data.attempt_number,
        response_normalized=event_data.response_normalized,
        is_correct=event_data.is_correct,
        hint_used=event_data.hint_used,
        difficulty_at_time=event_data.difficulty_at_time,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.post("/sessions/{session_id}/end", response_model=ActivitySessionResponse)
def end_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    End an activity session and trigger metrics recalculation.
    """
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session already ended")

    # Update session
    session.ended_at = datetime.utcnow()
    session.status = "completed"
    db.commit()
    db.refresh(session)

    # Trigger metrics recalculation (async in production, sync for MVP)
    try:
        metric_service.recalculate_and_save_metrics(
            db, session.student_id, session.subject_id, session.term_id
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error recalculating metrics: {e}")

    return session
