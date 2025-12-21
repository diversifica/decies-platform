from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.db import get_db
from app.models.role import Role
from app.models.student import Student
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.auth import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_role_name(db: Session, user: User) -> str:
    if not user.role_id:
        return ""
    role = db.get(Role, user.role_id)
    return (role.name if role else "").casefold()


def require_roles(db: Session, user: User, allowed: set[str]) -> str:
    role_name = get_current_role_name(db, user)
    if role_name not in {r.casefold() for r in allowed}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return role_name


def get_current_tutor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Tutor:
    require_roles(db, current_user, {"tutor"})
    tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return tutor


def get_current_student(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Student:
    require_roles(db, current_user, {"student"})
    student = (
        db.query(Student)
        .filter((Student.user_id == current_user.id) | (Student.id == current_user.id))
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def get_current_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    require_roles(db, current_user, {"admin"})
    return current_user
