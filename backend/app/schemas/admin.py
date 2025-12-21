import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminItemSummary(BaseModel):
    id: uuid.UUID
    content_upload_id: uuid.UUID
    microconcept_id: uuid.UUID | None = None
    type: str
    stem: str
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminRecommendationCatalogResponse(BaseModel):
    code: str
    title: str
    description: str
    category: str
    active: bool
    catalog_version: str

    model_config = ConfigDict(from_attributes=True)


class AdminRecommendationCatalogUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    active: bool | None = None
    catalog_version: str | None = None


class AdminActivityTypeUpdate(BaseModel):
    name: str | None = None
    active: bool | None = None
