"""
DECIES Platform - FastAPI Main Application
Sprint 0 - Día 1: Health endpoint only
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1 import auth, events
from app.core.db import get_db
from app.routers import activity, content, metrics, microconcepts, recommendations, reports

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
