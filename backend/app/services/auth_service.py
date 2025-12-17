from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import Login


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, login_data: Login) -> Optional[User]:
        stmt = select(User).where(User.email == login_data.email)
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            return None

        if not verify_password(login_data.password, user.hashed_password):
            return None

        return user
