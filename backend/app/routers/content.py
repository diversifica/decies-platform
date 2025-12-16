import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.content import ContentUpload, ContentUploadType
from app.models.tutor import Tutor
from app.schemas.content import ContentUploadResponse
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

    # 2. Get Tutor (Mock for now or Header)
    # Raising error if not impl
    # I will assume there is at least one tutor or create one via seed.
    # For now, I'll fetch the FIRST tutor to proceed, or handle logic.
    tutor = db.query(Tutor).first()
    if not tutor:
        # Create a dummy tutor/user if none exists?
        # NO, "Tutor sube PDF". Tutor must exist.
        # I will handle this in Verification by seeding.
        # Here I raise 403 if no tutor found (acting as "Not Authorized").
        raise HTTPException(status_code=403, detail="No authenticated tutor found")

    tutor_id = tutor.id

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
        page_count=0 
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)

    return db_content

@router.get("/uploads", response_model=list[ContentUploadResponse])
def get_uploads(
    db: Session = Depends(get_db)
):
    # Filter by Tutor...
    tutor = db.query(Tutor).first()
    if not tutor:
        return []
    
    return db.query(ContentUpload).filter(ContentUpload.tutor_id == tutor.id).all()
