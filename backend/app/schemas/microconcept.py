import uuid
from datetime import datetime

from pydantic import BaseModel


class MicroConceptBase(BaseModel):
    subject_id: uuid.UUID
    term_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    code: str | None = None
    name: str
    description: str | None = None
    active: bool = True


class MicroConceptCreate(MicroConceptBase):
    pass


class MicroConceptUpdate(BaseModel):
    term_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class MicroConceptResponse(MicroConceptBase):
    id: uuid.UUID
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class MicroConceptPrerequisiteBase(BaseModel):
    microconcept_id: uuid.UUID
    prerequisite_microconcept_id: uuid.UUID


class MicroConceptPrerequisiteCreate(MicroConceptPrerequisiteBase):
    pass


class MicroConceptPrerequisiteResponse(MicroConceptPrerequisiteBase):
    id: uuid.UUID
    created_at: datetime | None

    class Config:
        from_attributes = True
