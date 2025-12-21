from sqlalchemy.orm import Session

from app.models.events import LearningEvent
from app.schemas.events import EventCreate


class EventService:
    @staticmethod
    def create_event(db: Session, event_in: EventCreate) -> LearningEvent:
        db_event = LearningEvent(
            student_id=event_in.student_id,
            event_type=event_in.event_type,
            payload=event_in.payload,
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
