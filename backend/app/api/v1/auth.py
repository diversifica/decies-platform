from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_active_user
from app.models.role import Role
from app.models.student import Student
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.auth import Login, Token, UserMe
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    login_data: Login,
    db: Session = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = AuthService.authenticate_user(db, login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token_expires = timedelta(seconds=settings.JWT_EXPIRES_SECONDS)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/auth/me", response_model=UserMe)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserMe:
    role_name: str | None = None
    if current_user.role_id:
        role = db.get(Role, current_user.role_id)
        if role:
            role_name = role.name

    tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
    student = (
        db.query(Student)
        .filter((Student.user_id == current_user.id) | (Student.id == current_user.id))
        .first()
    )

    return UserMe(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=role_name,
        tutor_id=tutor.id if tutor else None,
        student_id=student.id if student else None,
    )
