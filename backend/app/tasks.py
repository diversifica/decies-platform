from __future__ import annotations

import logging
import uuid
from datetime import datetime

from app.core.db import SessionLocal
from app.models.content import ContentUpload
from app.pipelines.processing import process_content_upload
from app.services.metric_service import metric_service
from app.services.recommendation_service import recommendation_service

logger = logging.getLogger(__name__)


def process_upload_job(upload_id: str) -> None:
    upload_uuid = uuid.UUID(upload_id)
    db = SessionLocal()
    try:
        upload = db.query(ContentUpload).filter(ContentUpload.id == upload_uuid).first()
        if upload:
            upload.processing_status = "running"
            upload.processing_error = None
            upload.processed_at = None
            db.add(upload)
            db.commit()

        process_content_upload(db, upload_uuid)
        upload = db.query(ContentUpload).filter(ContentUpload.id == upload_uuid).first()
        if upload:
            upload.processing_status = "succeeded"
            upload.processing_error = None
            upload.processed_at = datetime.utcnow()
            db.add(upload)
            db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        upload = db.query(ContentUpload).filter(ContentUpload.id == upload_uuid).first()
        if upload:
            upload.processing_status = "failed"
            upload.processing_error = str(e)
            db.add(upload)
            db.commit()
        raise
    finally:
        db.close()


def recalculate_metrics_job(student_id: str, subject_id: str, term_id: str) -> None:
    student_uuid = uuid.UUID(student_id)
    subject_uuid = uuid.UUID(subject_id)
    term_uuid = uuid.UUID(term_id)

    db = SessionLocal()
    try:
        metric_service.recalculate_and_save_metrics(db, student_uuid, subject_uuid, term_uuid)
        recommendation_service.generate_recommendations(db, student_uuid, subject_uuid, term_uuid)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("Failed to recalculate metrics/recommendations")
        raise
    finally:
        db.close()
