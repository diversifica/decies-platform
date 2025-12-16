import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ContentUploadType(str, Enum):
    pdf = "pdf"
    image = "image"


class ContentUploadBase(BaseModel):
    subject_id: uuid.UUID
    term_id: uuid.UUID
    topic_id: uuid.UUID | None = None
    upload_type: ContentUploadType


class ContentUploadCreate(ContentUploadBase):
    pass
    # file is handled via UploadFile, not Pydantic model in the body directly for Form data


class ContentUploadResponse(ContentUploadBase):
    id: uuid.UUID
    tutor_id: uuid.UUID
    student_id: uuid.UUID | None
    storage_uri: str
    file_name: str
    mime_type: str
    page_count: int | None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
