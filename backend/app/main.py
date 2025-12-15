"""
DECIES Platform - FastAPI Main Application
Sprint 0 - Día 1: Health endpoint only
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DECIES API",
    description="Sistema de análisis y recomendaciones pedagógicas adaptativas",
    version="0.1.0"
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
        "status": "running"
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}
