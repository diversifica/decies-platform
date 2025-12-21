import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class Login(BaseModel):
    email: EmailStr
    password: str


class UserMe(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    role: str | None = None
    tutor_id: uuid.UUID | None = None
    student_id: uuid.UUID | None = None
