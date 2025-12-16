"""
DECIES Platform - FastAPI Main Application
Sprint 0 - Día 1: Health endpoint only
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db

app = FastAPI(
    title="DECIES API",
    description="Sistema de análisis y recomendaciones pedagógicas adaptativas",
    version="0.1.0",
)

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
