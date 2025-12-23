import logging
import os
import re
import uuid

import pypdf
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_versioning import (
    LLM_ENGINE_VERSION,
    PROMPT_VERSION_E2_STRUCTURE,
    PROMPT_VERSION_E3_MAP,
    PROMPT_VERSION_E5_VALIDATE,
)
from app.models.content import ContentUpload
from app.models.game import Game
from app.models.item import Item, ItemType
from app.models.knowledge import KnowledgeChunk, KnowledgeEntry
from app.models.llm_run import LLMRun, LLMRunStep
from app.models.microconcept import MicroConcept
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

E2_SEGMENT_MAX_CHARS = 18_000
E2_SEGMENT_MIN_CHARS = 8_000
E2_SEGMENT_MAX_COUNT = 12
LLM_MAX_ATTEMPTS = 2

E2_QUALITY_MIN_COVERAGE = 0.6
E5_QUALITY_MIN_KEEP_RATIO = 0.7


def _segment_raw_text(text: str) -> list[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    if len(cleaned) <= E2_SEGMENT_MAX_CHARS:
        return [cleaned]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned]

    segments: list[str] = []
    current: list[str] = []
    current_len = 0

    def _flush() -> None:
        nonlocal current, current_len
        if current:
            segments.append("\n\n".join(current).strip())
            current = []
            current_len = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph) + 2
        if (
            current
            and current_len + paragraph_len > E2_SEGMENT_MAX_CHARS
            and current_len >= E2_SEGMENT_MIN_CHARS
        ):
            _flush()

        if paragraph_len > E2_SEGMENT_MAX_CHARS:
            _flush()
            for i in range(0, len(paragraph), E2_SEGMENT_MAX_CHARS):
                segments.append(paragraph[i : i + E2_SEGMENT_MAX_CHARS].strip())
            continue

        current.append(paragraph)
        current_len += paragraph_len

    _flush()

    if len(segments) > E2_SEGMENT_MAX_COUNT:
        segments = segments[:E2_SEGMENT_MAX_COUNT]

    return [s for s in segments if s]


def _compute_e2_quality(*, raw_text: str, chunks: list[str], llm_quality: dict | None) -> dict:
    raw_len = max(1, len(raw_text))
    chunks_len = sum(len(c) for c in chunks if c)
    coverage = min(1.0, max(0.0, chunks_len / raw_len))

    coherence = 1.0
    if not chunks:
        coherence = 0.0
    elif len(chunks) > 30:
        coherence = 0.6

    hallucination_risk = "low"
    if not chunks:
        hallucination_risk = "high"
    elif raw_len >= 2_000:
        if coverage < 0.1:
            hallucination_risk = "high"
        elif coverage < E2_QUALITY_MIN_COVERAGE:
            hallucination_risk = "medium"

    ambiguity_risk = "low"
    if len(chunks) > 25:
        ambiguity_risk = "medium"
    if len(chunks) > 40:
        ambiguity_risk = "high"

    if llm_quality:
        coverage = float(llm_quality.get("coverage", coverage))
        coherence = float(llm_quality.get("coherence", coherence))
        hallucination_risk = str(llm_quality.get("hallucination_risk", hallucination_risk))
        ambiguity_risk = str(llm_quality.get("ambiguity_risk", ambiguity_risk))

    def _norm_risk(value: str) -> str:
        v = (value or "").strip().lower()
        return v if v in {"low", "medium", "high"} else "medium"

    return {
        "coverage": max(0.0, min(1.0, coverage)),
        "coherence": max(0.0, min(1.0, coherence)),
        "hallucination_risk": _norm_risk(hallucination_risk),
        "ambiguity_risk": _norm_risk(ambiguity_risk),
    }


def _log_llm_attempt(
    db: Session,
    *,
    upload_id: uuid.UUID,
    step: LLMRunStep,
    model: str,
    attempt: int,
    prompt_version: str,
    engine_version: str,
    status: str,
    error_message: str | None = None,
    knowledge_entry_id: uuid.UUID | None = None,
    knowledge_chunk_id: uuid.UUID | None = None,
    subfolder: str | None = None,
    game_code: str | None = None,
) -> None:
    run = LLMRun(
        step=step,
        model=model,
        status=status,
        subfolder=subfolder,
        attempt=attempt,
        prompt_version=prompt_version,
        engine_version=engine_version,
        error_message=error_message,
        content_upload_id=upload_id,
        knowledge_entry_id=knowledge_entry_id,
        knowledge_chunk_id=knowledge_chunk_id,
        game_code=game_code,
    )
    db.add(run)


def _call_with_retries(
    db: Session,
    *,
    upload_id: uuid.UUID,
    step: LLMRunStep,
    model: str,
    prompt_version: str,
    engine_version: str,
    subfolder: str | None,
    knowledge_entry_id: uuid.UUID | None,
    knowledge_chunk_id: uuid.UUID | None,
    game_code: str | None,
    fn,
):
    last_exc: Exception | None = None
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        try:
            result = fn()
            _log_llm_attempt(
                db,
                upload_id=upload_id,
                step=step,
                model=model,
                attempt=attempt,
                prompt_version=prompt_version,
                engine_version=engine_version,
                status="success",
                subfolder=subfolder,
                knowledge_entry_id=knowledge_entry_id,
                knowledge_chunk_id=knowledge_chunk_id,
                game_code=game_code,
            )
            return result
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            _log_llm_attempt(
                db,
                upload_id=upload_id,
                step=step,
                model=model,
                attempt=attempt,
                prompt_version=prompt_version,
                engine_version=engine_version,
                status="failed",
                error_message=str(exc),
                subfolder=subfolder,
                knowledge_entry_id=knowledge_entry_id,
                knowledge_chunk_id=knowledge_chunk_id,
                game_code=game_code,
            )
    assert last_exc is not None
    raise last_exc


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
    Orchestrates the LLM pipeline (E2 + E3 + E4) for a given upload.
    """
    logger.info(f"Starting processing for upload {upload_id}")

    # 1. Fetch Upload
    upload = db.query(ContentUpload).filter(ContentUpload.id == upload_id).first()
    if not upload:
        raise ValueError("Upload not found")

    default_microconcept = (
        db.query(MicroConcept)
        .filter(
            MicroConcept.subject_id == upload.subject_id,
            MicroConcept.term_id == upload.term_id,
            MicroConcept.active.is_(True),
        )
        .order_by(MicroConcept.created_at.asc())
        .first()
    )
    if not default_microconcept:
        default_microconcept = MicroConcept(
            id=uuid.uuid4(),
            subject_id=upload.subject_id,
            term_id=upload.term_id,
            topic_id=None,
            code=None,
            name="General",
            description="Microconcepto genérico (auto)",
            active=True,
        )
        db.add(default_microconcept)
        db.flush()

    microconcepts = (
        db.query(MicroConcept)
        .filter(
            MicroConcept.subject_id == upload.subject_id,
            MicroConcept.active.is_(True),
            or_(MicroConcept.term_id == upload.term_id, MicroConcept.term_id.is_(None)),
        )
        .order_by(MicroConcept.created_at.asc())
        .all()
    )
    microconcept_ids = {mc.id for mc in microconcepts}

    # Translate relative path to absolute if needed
    # (Assuming StorageService behaves consistently, here we need absolute file path to open)
    # The DB path is like "uploads/xyz.pdf".
    # In Docker: /app/storage/uploads/xyz.pdf
    # Locally: e:\...\backend\storage\uploads\xyz.pdf
    # We'll use a helper or assume default root.

    # Better: Use StorageService to get full path if method existed, or construct it.
    # For now, simplistic approach:
    base_path = "storage"  # Relative to backend/ workdir
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

    # 3. E2: Structure (segmented if raw_text is large)
    logger.info("Running E2: Structure")
    try:
        segments = _segment_raw_text(raw_text)
        if not segments:
            logger.warning("No segments produced from raw_text")
            return

        segment_results = []
        for idx, segment in enumerate(segments):
            segment_results.append(
                _call_with_retries(
                    db,
                    upload_id=upload.id,
                    step=LLMRunStep.E2_STRUCTURE,
                    model=settings.LLM_MODEL_NAME,
                    prompt_version=PROMPT_VERSION_E2_STRUCTURE,
                    engine_version=LLM_ENGINE_VERSION,
                    subfolder=f"segment:{idx}",
                    knowledge_entry_id=None,
                    knowledge_chunk_id=None,
                    game_code=None,
                    fn=lambda s=segment: llm_service.generate_structure_e2(s),
                )
            )

        merged_summary = "\n\n".join(
            r.summary.strip() for r in segment_results if r.summary
        ).strip()
        merged_chunks: list[str] = []
        for result in segment_results:
            merged_chunks.extend([c for c in (result.chunks or []) if (c or "").strip()])

        e2_quality = _compute_e2_quality(
            raw_text=raw_text,
            chunks=merged_chunks,
            llm_quality=segment_results[0].quality if segment_results else None,
        )

        entry = KnowledgeEntry(
            content_upload_id=upload.id,
            summary=merged_summary,
            structure_json={
                "segments_count": len(segments),
                "chunks_count": len(merged_chunks),
                "quality": e2_quality,
            },
        )
        db.add(entry)
        db.flush()

        chunks: list[KnowledgeChunk] = []
        for i, chunk_text in enumerate(merged_chunks):
            chunk = KnowledgeChunk(knowledge_entry_id=entry.id, content=chunk_text, index=i)
            db.add(chunk)
            chunks.append(chunk)

        db.flush()

    except Exception as e:
        logger.error(f"E2 failed: {e}")
        db.commit()
        raise

    if e2_quality.get("hallucination_risk") == "high":
        logger.warning(
            "E2 quality gate blocked: hallucination_risk=high; skipping item generation."
        )
        db.commit()
        return

    # 4. E3: Map chunks to microconcepts
    logger.info("Running E3: Map")
    e3_min_confidence = 0.6

    microconcept_catalog = [
        {"id": str(mc.id), "code": mc.code, "name": mc.name} for mc in microconcepts
    ]
    chunks_from_e2 = [{"chunk_type": "chunk", "content": chunk.content} for chunk in chunks]

    try:
        e3_result = _call_with_retries(
            db,
            upload_id=upload.id,
            step=LLMRunStep.E3_MAP,
            model=settings.LLM_MODEL_NAME,
            prompt_version=PROMPT_VERSION_E3_MAP,
            engine_version=LLM_ENGINE_VERSION,
            subfolder=None,
            knowledge_entry_id=entry.id,
            knowledge_chunk_id=None,
            game_code=None,
            fn=lambda: llm_service.map_chunks_to_microconcepts_e3(
                microconcept_catalog=microconcept_catalog,
                chunks_from_e2=chunks_from_e2,
            ),
        )

        mapping_by_index = {m.chunk_index: m for m in e3_result.chunk_mappings}
        for chunk in chunks:
            mapping = mapping_by_index.get(chunk.index)
            if not mapping:
                continue
            mapped_id = mapping.microconcept_match.microconcept_id
            if not mapped_id:
                continue
            if mapping.confidence < e3_min_confidence:
                continue
            if mapped_id not in microconcept_ids:
                continue
            chunk.microconcept_id = mapped_id

        db.flush()

    except Exception as e:
        logger.error(f"E3 failed: {e}")

    # 5. E4: Generate candidate items (multi-game)
    logger.info("Running E4: Items (multi-game)")

    # Query active games
    active_games = db.query(Game).filter(Game.active == True).all()  # noqa: E712
    if not active_games:
        logger.warning("No active games found, skipping item generation")
        db.commit()
        return

    logger.info(f"Found {len(active_games)} active games: {[g.code for g in active_games]}")

    microconcept_by_id = {mc.id: mc for mc in microconcepts}
    candidate_items: list[dict] = []

    # Iterate over each active game
    for game in active_games:
        logger.info(f"Generating items for game: {game.code} ({game.name})")

        for chunk in chunks:
            try:
                # For now, we'll use the existing generate_items_e4 method
                # In a future iteration, we could use game.prompt_template
                # to customize the prompt per game
                e4_result = _call_with_retries(
                    db,
                    upload_id=upload.id,
                    step=LLMRunStep.E4_ITEMS,
                    model=settings.LLM_MODEL_NAME,
                    prompt_version=game.prompt_version,
                    engine_version=game.engine_version,
                    subfolder=f"{game.code}:{chunk.id}",
                    knowledge_entry_id=entry.id,
                    knowledge_chunk_id=chunk.id,
                    game_code=game.code,
                    fn=lambda c=chunk.content: llm_service.generate_items_e4(c, quantity=2),
                )

                chunk_microconcept_id = chunk.microconcept_id or default_microconcept.id
                microconcept = microconcept_by_id.get(chunk_microconcept_id)

                microconcept_ref = {
                    "microconcept_id": str(chunk_microconcept_id)
                    if chunk_microconcept_id
                    else None,
                    "microconcept_code": microconcept.code if microconcept else None,
                    "microconcept_name": microconcept.name if microconcept else None,
                }

                for item_data in e4_result.items:
                    item_type = "mcq" if item_data["type"] == "multiple_choice" else "true_false"
                    candidate_items.append(
                        {
                            "item_type": item_type,
                            "stem": item_data["stem"],
                            "options": item_data.get("options"),
                            "correct_answer": item_data["correct_answer"],
                            "explanation": item_data.get("explanation"),
                            "difficulty": 1.0,
                            "microconcept_ref": microconcept_ref,
                            "source_chunk_index": chunk.index,
                            "source_game": game.code,  # NEW: Track which game generated this item
                        }
                    )

            except Exception as e:
                logger.error(f"E4 failed for game {game.code}, chunk {chunk.id}: {e}")
                continue

    # 6. E5: Validate/filter candidate items
    logger.info("Running E5: Validate")

    if not candidate_items:
        db.commit()
        logger.info("No candidate items generated")
        return

    try:
        e5_result = _call_with_retries(
            db,
            upload_id=upload.id,
            step=LLMRunStep.E5_VALIDATE,
            model=settings.LLM_MODEL_NAME,
            prompt_version=PROMPT_VERSION_E5_VALIDATE,
            engine_version=LLM_ENGINE_VERSION,
            subfolder=None,
            knowledge_entry_id=entry.id,
            knowledge_chunk_id=None,
            game_code=None,
            fn=lambda: llm_service.validate_items_e5(
                items=candidate_items,
                chunks_from_e2=chunks_from_e2,
            ),
        )

        validated_by_index = {v.index: v for v in e5_result.validated_items}
        total_candidates = len(candidate_items)
        kept_count = 0
        for idx in range(total_candidates):
            validated = validated_by_index.get(idx)
            if validated and validated.status in {"ok", "fix"}:
                kept_count += 1

        keep_ratio = kept_count / total_candidates if total_candidates else 0.0
        gate_failed = keep_ratio < E5_QUALITY_MIN_KEEP_RATIO
        gate_note = None
        if gate_failed:
            gate_note = f"keep_ratio_gate({kept_count}/{total_candidates})"
            logger.warning(
                "E5 quality gate triggered: keep_ratio=%s (<%s); marking all items inactive.",
                keep_ratio,
                E5_QUALITY_MIN_KEEP_RATIO,
            )

        for idx in range(total_candidates):
            candidate = candidate_items[idx]
            validated = validated_by_index.get(idx)

            if validated is None:
                status = "drop"
                reason = "missing_validation"
                stem = candidate.get("stem")
                options = candidate.get("options")
                correct_answer = candidate.get("correct_answer")
                explanation = candidate.get("explanation")
                difficulty_value = candidate.get("difficulty", 1.0)
                source_chunk_index = candidate.get("source_chunk_index")
                item_type = candidate.get("item_type")
                microconcept_id = None
                candidate_mc_id = candidate.get("microconcept_ref", {}).get("microconcept_id")
                if candidate_mc_id:
                    try:
                        microconcept_id = uuid.UUID(candidate_mc_id)
                    except ValueError:
                        microconcept_id = None
            else:
                status = validated.status
                reason = validated.reason
                stem = validated.item.stem
                options = validated.item.options
                correct_answer = validated.item.correct_answer
                explanation = validated.item.explanation
                difficulty_value = validated.item.difficulty or 1.0
                source_chunk_index = validated.item.source_chunk_index
                item_type = validated.item.item_type
                microconcept_id = validated.item.microconcept_ref.microconcept_id
                if microconcept_id and microconcept_id not in microconcept_ids:
                    microconcept_id = None
                if not microconcept_id:
                    candidate_mc_id = candidate.get("microconcept_ref", {}).get("microconcept_id")
                    if candidate_mc_id:
                        try:
                            parsed = uuid.UUID(candidate_mc_id)
                        except ValueError:
                            parsed = None
                        if parsed and parsed in microconcept_ids:
                            microconcept_id = parsed

            if gate_note:
                reason = f"{reason} | {gate_note}" if reason else gate_note

            itype = ItemType.TRUE_FALSE if item_type == "true_false" else ItemType.MCQ

            difficulty = int(round(difficulty_value or 1.0))
            difficulty = max(1, min(3, difficulty))

            is_active = (status != "drop") and (not gate_failed)

            item = Item(
                content_upload_id=upload.id,
                microconcept_id=microconcept_id or default_microconcept.id,
                type=itype,
                stem=stem,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
                difficulty=difficulty,
                source_chunk_index=source_chunk_index,
                validation_status=status,
                validation_reason=reason,
                is_active=is_active,
                source_game=candidate.get("source_game"),  # NEW: Store which game generated this
            )
            db.add(item)

    except Exception as e:
        logger.error(f"E5 failed: {e}")
        for candidate in candidate_items:
            itype = ItemType.MCQ if candidate["item_type"] == "mcq" else ItemType.TRUE_FALSE
            item = Item(
                content_upload_id=upload.id,
                microconcept_id=default_microconcept.id,
                type=itype,
                stem=candidate["stem"],
                options=candidate.get("options"),
                correct_answer=candidate["correct_answer"],
                explanation=candidate.get("explanation"),
                difficulty=1,
                source_chunk_index=candidate.get("source_chunk_index"),
                validation_status=None,
                validation_reason="E5 failed",
                is_active=True,
                source_game=candidate.get("source_game"),  # NEW: Store which game generated this
            )
            db.add(item)

    db.commit()
    logger.info("Processing complete")
