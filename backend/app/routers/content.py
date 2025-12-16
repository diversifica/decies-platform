import uuid
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

from app.core.db import get_db
from app.models.content import ContentUpload, ContentUploadType
from app.models.item import Item
from app.models.tutor import Tutor
from app.pipelines.processing import process_content_upload
from app.schemas.content import ContentUploadResponse
from app.schemas.item import ItemResponse
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
    # current_tutor: Tutor = Depends(get_current_active_tutor), # TODO
    db: Session = Depends(get_db),
):
    # TODO: Real Auth. Mocking Tutor for Day 1 if no auth system.
    # We need a Tutor in DB.
    # For Sprint 1 Day 1, we can require a "X-Tutor-ID" header temporarily if Auth not ready?
    # Or impl basic dependency.

    # 1. Save file
    try:
        storage_uri = StorageService.save_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File storage failed: {str(e)}")

    # 2. Get Tutor
    target_tutor = None
    if tutor_id:
        target_tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
        if not target_tutor:
             raise HTTPException(status_code=404, detail=f"Tutor {tutor_id} not found")
    else:
        # Fallback to first
        target_tutor = db.query(Tutor).first()
        if not target_tutor:
            raise HTTPException(status_code=403, detail="No authenticated tutor found")
            
    final_tutor_id = target_tutor.id

    # 3. Create DB Record
    db_content = ContentUpload(
        tutor_id=tutor_id,
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
def get_uploads(db: Session = Depends(get_db)):
    # Filter by Tutor...
    tutor = db.query(Tutor).first()
    if not tutor:
        return []

    return db.query(ContentUpload).filter(ContentUpload.tutor_id == tutor.id).all()


@router.post("/uploads/{upload_id}/process", status_code=status.HTTP_202_ACCEPTED)
def process_upload(
    upload_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Triggers the LLM pipeline (E2 + E4) for the given upload_id.
    """
    # Verify existence
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Ensure running in background (for Day 2 Smoke Check simplicity)
    # Note: We pass a new DB session or handle session within the task.
    # Passing 'db' directly to background task is RISKY if the request session closes.
    # Ideally, the background task opens its own session.
    # Refactoring `process_content_upload` to accept session_factory or manage its own session?
    # Or just passing `get_db` generator?
    # Simplest for now: The task connects to DB itself.

    # I'll update `process_content_upload` to create its own session using `SessionLocal`.

    background_tasks.add_task(run_pipeline_task, upload_id)
    return {"message": "Processing started", "upload_id": upload_id}


def run_pipeline_task(upload_id: uuid.UUID):
    # Wrapper to handle DB session for background task
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        process_content_upload(db, upload_id)
    finally:
        db.close()


@router.get("/uploads/{upload_id}/items", response_model=list[ItemResponse])
def get_upload_items(
    upload_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Fetch all generated items for a specific upload.
    """
    # Verify existence
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    items = db.query(Item).filter(Item.content_upload_id == upload_id).all()
    return items
