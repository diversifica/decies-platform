from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventBase(BaseModel):
    event_type: str
    payload: dict[str, Any]


class EventCreate(EventBase):
    student_id: UUID


class EventResponse(EventBase):
    id: UUID
    student_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
