import logging
import os
import uuid

import pypdf
from sqlalchemy.orm import Session

from app.models.content import ContentUpload
from app.models.item import Item, ItemType
from app.models.knowledge import KnowledgeChunk, KnowledgeEntry
from app.models.llm_run import LLMRun, LLMRunStep
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        raise
    return text


def process_content_upload(db: Session, upload_id: uuid.UUID):
    """
    Orchestrates the LLM pipeline (E2 + E4) for a given upload.
    """
    logger.info(f"Starting processing for upload {upload_id}")
    
    # 1. Fetch Upload
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise ValueError("Upload not found")
        
    # Translate relative path to absolute if needed
    # (Assuming StorageService behaves consistently, here we need absolute file path to open)
    # The DB path is like "uploads/xyz.pdf".
    # In Docker: /app/storage/uploads/xyz.pdf
    # Locally: e:\...\backend\storage\uploads\xyz.pdf
    # We'll use a helper or assume default root.
    
    # Better: Use StorageService to get full path if method existed, or construct it.
    # For now, simplistic approach:
    base_path = "storage" # Relative to backend/ workdir
    file_path = os.path.join(base_path, upload.storage_uri)
    
    if not os.path.exists(file_path):
        # Fallback for absolute path (legacy) or full path check
        if os.path.exists(f"/app/storage/{upload.storage_uri}"):
             file_path = f"/app/storage/{upload.storage_uri}"
        else:
             raise FileNotFoundError(f"File not found at {file_path}")

    # 2. Extract Text
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text.strip():
        logger.warning("Empty text extracted")
        return

    llm_service = LLMService()

    # 3. E2: Structure
    logger.info("Running E2: Structure")
    try:
        e2_result = llm_service.generate_structure_e2(raw_text)
        
        # Log Run (Simplistic cost tracking)
        run_e2 = LLMRun(
            step=LLMRunStep.E2_STRUCTURE,
            model="gpt-4-turbo-preview",  # hardcoded or from settings
            status="success"
        )
        db.add(run_e2)
        
        # Save Entry
        entry = KnowledgeEntry(
            content_upload_id=upload.id,
            summary=e2_result.summary,
            structure_json={"chunks_count": len(e2_result.chunks)}
        )
        db.add(entry)
        db.flush()
        
        # Save Chunks
        chunks = []
        for i, chunk_text in enumerate(e2_result.chunks):
            chunk = KnowledgeChunk(
                knowledge_entry_id=entry.id,
                content=chunk_text,
                index=i
            )
            db.add(chunk)
            chunks.append(chunk) # Keep ref for E4
            
        db.flush()
        
    except Exception as e:
        logger.error(f"E2 failed: {e}")
        # Log failure
        run_e2 = LLMRun(step=LLMRunStep.E2_STRUCTURE, model="unknown", status="failed")
        db.add(run_e2)
        db.commit()
        raise

    # 4. E4: Items (for each chunk)
    logger.info("Running E4: Items")
    for chunk in chunks:
        try:
            e4_result = llm_service.generate_items_e4(chunk.content, quantity=2) # 2 items per chunk
            
            # Log Run
            run_e4 = LLMRun(
                step=LLMRunStep.E4_ITEMS,
                model="gpt-4-turbo-preview",
                status="success",
                subfolder=str(chunk.id)
            )
            db.add(run_e4)
            
            # Save Items
            for item_data in e4_result.items:
                # Map string type to Enum
                itype = ItemType.MCQ if item_data["type"] == "multiple_choice" else ItemType.TRUE_FALSE
                
                item = Item(
                    content_upload_id=upload.id,
                    type=itype,
                    stem=item_data["stem"],
                    options=item_data.get("options"),
                    correct_answer=item_data["correct_answer"],
                    explanation=item_data.get("explanation")
                )
                db.add(item)
                
        except Exception as e:
            logger.error(f"E4 failed for chunk {chunk.id}: {e}")
            # Continue with other chunks
            
    db.commit()
    logger.info("Processing complete")
