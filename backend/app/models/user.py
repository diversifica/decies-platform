from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="users_email_key"),
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("roles.id", name="users_role_id_fkey"), nullable=True
    )
    is_active: Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("true"), nullable=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )
