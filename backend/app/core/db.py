from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.models import (  # noqa: E402, F401, I001
    activity,
    content,
    item,
    knowledge,
    llm_run,
    metric,
    microconcept,
    report,
    role,
    student,
    subject,
    term,
    topic,
    tutor,
    user,
    recommendation,
)
