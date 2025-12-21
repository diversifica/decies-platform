import uuid
from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import (
    get_current_active_user,
    get_current_role_name,
    get_current_student,
    get_current_tutor,
)
from app.core.queue import enqueue_upload_processing, is_async_queue_enabled
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item
from app.models.subject import Subject
from app.models.tutor import Tutor
from app.models.user import User
from app.pipelines.processing import process_content_upload
from app.schemas.content import ContentUploadResponse
from app.schemas.item import ItemActivationUpdate, ItemResponse
from app.services.storage import StorageService

# TODO: Auth dependency to get current user/tutor
# For now, we mock auth or assume header?
# The task says: "validar rol TUTOR".
# I need a dependency `get_current_tutor`.
# Since "Sprint 0" might not have Auth implemented fully, I check if `app.api.deps` exists?
# I'll check `app/api` folder content first.
# For now I write the code assuming a placeholder dependency or basic check.

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/uploads", response_model=ContentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_content(
    subject_id: Annotated[uuid.UUID, Form()],
    term_id: Annotated[uuid.UUID, Form()],
    upload_type: Annotated[ContentUploadType, Form()],
    file: Annotated[UploadFile, File()],
    topic_id: Annotated[uuid.UUID | None, Form()] = None,
    tutor_id: Annotated[uuid.UUID | None, Form()] = None,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    if tutor_id and tutor_id != current_tutor.id:
        raise HTTPException(status_code=403, detail="Tutor mismatch")

    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.tutor_id and subject.tutor_id != current_tutor.user_id:
        raise HTTPException(status_code=403, detail="Subject not owned by tutor")

    # 1. Save file
    try:
        storage_uri = StorageService.save_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File storage failed: {str(e)}")

    # 3. Create DB Record
    db_content = ContentUpload(
        tutor_id=current_tutor.id,
        subject_id=subject_id,
        term_id=term_id,
        topic_id=topic_id,
        upload_type=upload_type,
        storage_uri=storage_uri,
        file_name=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        page_count=0,
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)

    return db_content


@router.get("/uploads", response_model=list[ContentUploadResponse])
def get_uploads(
    tutor_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name == "tutor":
        current_tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
        if not current_tutor:
            return []
        if tutor_id and tutor_id != current_tutor.id:
            raise HTTPException(status_code=403, detail="Tutor mismatch")
        return db.query(ContentUpload).filter(ContentUpload.tutor_id == current_tutor.id).all()

    if role_name == "student":
        student = get_current_student(db=db, current_user=current_user)
        if not student.subject_id:
            return []
        return db.query(ContentUpload).filter(ContentUpload.subject_id == student.subject_id).all()

    raise HTTPException(status_code=403, detail="Role not allowed")


@router.post("/uploads/{upload_id}/process", status_code=status.HTTP_202_ACCEPTED)
def process_upload(
    upload_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    """
    Triggers the LLM pipeline (E2 + E4) for the given upload_id.
    """
    # Verify existence
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.tutor_id != current_tutor.id:
        raise HTTPException(status_code=403, detail="Upload not owned by tutor")

    # Ensure running in background (for Day 2 Smoke Check simplicity)
    # Note: We pass a new DB session or handle session within the task.
    # Passing 'db' directly to background task is RISKY if the request session closes.
    # Ideally, the background task opens its own session.
    # Refactoring `process_content_upload` to accept session_factory or manage its own session?
    # Or just passing `get_db` generator?
    # Simplest for now: The task connects to DB itself.

    # I'll update `process_content_upload` to create its own session using `SessionLocal`.

    upload.processing_error = None

    if is_async_queue_enabled():
        try:
            job_id = enqueue_upload_processing(upload_id=upload_id)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"Queue unavailable: {e}") from e

        upload.processing_status = "queued"
        upload.processing_job_id = job_id
        db.add(upload)
        db.commit()

        return {"message": "Processing enqueued", "upload_id": upload_id, "job_id": job_id}

    upload.processing_status = "queued"
    upload.processing_job_id = None
    db.add(upload)
    db.commit()

    background_tasks.add_task(run_pipeline_task, upload_id)
    return {"message": "Processing started", "upload_id": upload_id}


def run_pipeline_task(upload_id: uuid.UUID):
    # Wrapper to handle DB session for background task
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
        if upload:
            upload.processing_status = "running"
            upload.processing_error = None
            upload.processed_at = None
            db.add(upload)
            db.commit()

        process_content_upload(db, upload_id)

        upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
        if upload:
            upload.processing_status = "succeeded"
            upload.processing_error = None
            upload.processed_at = datetime.utcnow()
            db.add(upload)
            db.commit()
    except Exception as e:  # noqa: BLE001
        upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
        if upload:
            upload.processing_status = "failed"
            upload.processing_error = str(e)
            db.add(upload)
            db.commit()
        raise
    finally:
        db.close()


@router.get("/uploads/{upload_id}/processing")
def get_upload_processing_state(
    upload_id: uuid.UUID,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.tutor_id != current_tutor.id:
        raise HTTPException(status_code=403, detail="Upload not owned by tutor")

    status_value = upload.processing_status or "idle"
    return {
        "upload_id": upload_id,
        "status": status_value,
        "job_id": upload.processing_job_id,
        "error": upload.processing_error,
        "processed_at": upload.processed_at,
        "async_enabled": bool(settings.ASYNC_QUEUE_ENABLED),
    }


@router.get("/uploads/{upload_id}/items", response_model=list[ItemResponse])
def get_upload_items(
    upload_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all generated items for a specific upload.
    """
    # Verify existence
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    role_name = get_current_role_name(db, current_user)
    if role_name == "tutor":
        current_tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
        if not current_tutor or upload.tutor_id != current_tutor.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    elif role_name == "student":
        student = get_current_student(db=db, current_user=current_user)
        if not student.subject_id or upload.subject_id != student.subject_id:
            raise HTTPException(status_code=403, detail="Not allowed")
    else:
        raise HTTPException(status_code=403, detail="Role not allowed")

    query = db.query(Item).filter(Item.content_upload_id == upload_id)
    if role_name == "student":
        query = query.filter(Item.is_active.is_(True))
    items = query.all()
    return items


@router.patch("/uploads/{upload_id}/items/{item_id}", response_model=ItemResponse)
def set_item_active_state(
    upload_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: ItemActivationUpdate,
    current_tutor: Tutor = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    """
    Tutor-only: activate/deactivate an item belonging to an upload.
    """
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.tutor_id != current_tutor.id:
        raise HTTPException(status_code=403, detail="Upload not owned by tutor")

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item or item.content_upload_id != upload_id:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_active = payload.is_active
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
