from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.item import ItemType


class GameResponse(BaseModel):
    code: str
    name: str
    description: str | None = None
    item_type: ItemType
    prompt_template: str
    prompt_version: str
    engine_version: str
    source_hint: str | None = None
    active: bool
    last_processed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class GameUpdate(BaseModel):
    active: bool | None = None
