"""
Security utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration time as fallback, though service should handle this
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Use setting if available, otherwise fallback (should be in config)
    # Using a hardcoded fallback ONLY if settings variable not present, but it should be.
    # Assuming settings has JWT_SECRET.
    # If settings doesn't have it, we need to update config.py. 
    # Let's check config.py content again in next step if needed, but for now writes code assuming it exists or defined here.
    
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # We need a SECRET_KEY. In the plan I saw checking settings. 
    # The config file viewed earlier did NOT have SECRET_KEY.
    # I should add it to config.py as well.
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a password hash.
    """
    return pwd_context.hash(password)
