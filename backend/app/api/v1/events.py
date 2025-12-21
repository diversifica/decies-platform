from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.events import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter()


@router.post("/events/", response_model=EventResponse)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new learning event.
    """
    # Ideally should verify if current_user.id usually matches student_id or has permissions
    # For Sprint 0 we assume valid flow.
    return EventService.create_event(db, event_in)
