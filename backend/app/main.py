"""
DECIES Platform - FastAPI Main Application
Sprint 0 - Día 1: Health endpoint only
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError
from rq import Worker
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1 import auth, events
from app.core.config import settings
from app.core.db import get_db
from app.core.queue import _get_redis_connection
from app.routers import (
    activity,
    admin,
    catalog,
    content,
    grades,
    metrics,
    microconcepts,
    recommendations,
    reports,
)

app = FastAPI(
    title="DECIES API",
    description="Sistema de analisis y recomendaciones pedagogicas adaptativas",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(activity.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(microconcepts.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
app.include_router(grades.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "DECIES Platform API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Database health check endpoint"""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "database": "unavailable",
                "error": str(exc),
            },
        ) from exc

    return {"status": "ok", "db": "ok"}


@app.get("/health/redis")
def health_redis():
    """Redis health check endpoint (used for async queue mode)."""
    try:
        redis_connection = _get_redis_connection()
        redis_connection.ping()
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "redis": "unavailable",
                "error": str(exc),
            },
        ) from exc

    return {"status": "ok", "redis": "ok"}


@app.get("/health/worker")
def health_worker():
    """Worker health check endpoint (only meaningful when ASYNC_QUEUE_ENABLED=true)."""
    if not settings.ASYNC_QUEUE_ENABLED:
        return {"status": "skipped", "async_enabled": False}

    try:
        redis_connection = _get_redis_connection()
        redis_connection.ping()
        workers = Worker.all(connection=redis_connection)
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "redis": "unavailable",
                "error": str(exc),
            },
        ) from exc

    active_workers = []
    for worker in workers:
        try:
            if any(queue.name == settings.RQ_QUEUE_NAME for queue in worker.queues):
                active_workers.append(worker.name)
        except Exception:  # noqa: BLE001
            active_workers.append(worker.name)

    if not active_workers:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "worker": "unavailable",
                "queue": settings.RQ_QUEUE_NAME,
                "workers": 0,
            },
        )

    return {
        "status": "ok",
        "async_enabled": True,
        "queue": settings.RQ_QUEUE_NAME,
        "workers": len(active_workers),
    }
