from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.db import get_db
from app.schemas.auth import Login, Token
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
