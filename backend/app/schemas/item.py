import uuid
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.item import ItemType


class ItemBase(BaseModel):
    type: ItemType
    stem: str
    options: Any | None = None
    # correct_answer should be hidden potentially if we want server-side grading
    # But for MVP immediate feedback:
    correct_answer: str
    explanation: Optional[str] = None


class ItemCreate(ItemBase):
    content_upload_id: uuid.UUID


class ItemResponse(ItemBase):
    id: uuid.UUID
    content_upload_id: uuid.UUID
    microconcept_id: uuid.UUID | None = None
    is_active: bool = True
    source_game: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemActivationUpdate(BaseModel):
    is_active: bool
