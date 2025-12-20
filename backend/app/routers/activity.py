import json
import uuid
from datetime import datetime
from decimal import Decimal
from unicodedata import combining, normalize

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_active_user, get_current_role_name, get_current_student
from app.models.activity import (
    ActivitySession,
    ActivitySessionItem,
    ActivityType,
    LearningEvent,
)
from app.models.item import Item, ItemType
from app.models.metric import MasteryState
from app.models.microconcept import MicroConcept, MicroConceptPrerequisite
from app.models.student import Student
from app.models.subject import Subject
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.activity import (
    ActivitySessionCreate,
    ActivitySessionFeedbackCreate,
    ActivitySessionResponse,
    ActivityTypeResponse,
    LearningEventCreate,
    LearningEventResponse,
)
from app.schemas.item import ItemResponse
from app.services.metric_service import metric_service

router = APIRouter(prefix="/activities", tags=["activities"])

MAX_ITEMS_PER_MICROCONCEPT = 2
AT_RISK_PER_CYCLE = 2
PREREQ_PER_CYCLE = 1
IN_PROGRESS_PER_CYCLE = 1
MAX_PREREQ_MICROCONCEPTS = 2


def _to_float(value: float | Decimal | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _fetch_mastery_map(
    db: Session, *, student_id: uuid.UUID, microconcept_ids: set[uuid.UUID]
) -> dict[uuid.UUID, MasteryState]:
    if not microconcept_ids:
        return {}
    rows = (
        db.query(MasteryState)
        .filter(
            MasteryState.student_id == student_id,
            MasteryState.microconcept_id.in_(microconcept_ids),
        )
        .all()
    )
    return {ms.microconcept_id: ms for ms in rows}


def _adaptive_order_items_v1(
    items: list[Item], mastery_by_microconcept: dict[uuid.UUID, MasteryState]
) -> list[Item]:
    at_risk: list[tuple[float, uuid.UUID, Item]] = []
    in_progress: list[tuple[float, uuid.UUID, Item]] = []
    dominant: list[tuple[float, uuid.UUID, Item]] = []
    unknown: list[tuple[uuid.UUID, Item]] = []
    no_microconcept: list[Item] = []

    for item in items:
        if not item.microconcept_id:
            no_microconcept.append(item)
            continue

        ms = mastery_by_microconcept.get(item.microconcept_id)
        if not ms:
            unknown.append((item.id, item))
            continue

        score = _to_float(ms.mastery_score)
        key = (score, item.id, item)
        if ms.status == "at_risk":
            at_risk.append(key)
        elif ms.status == "in_progress":
            in_progress.append(key)
        elif ms.status == "dominant":
            dominant.append(key)
        else:
            unknown.append((item.id, item))

    at_risk.sort(key=lambda x: (x[0], x[1]))
    in_progress.sort(key=lambda x: (x[0], x[1]))
    dominant.sort(key=lambda x: (x[0], x[1]))
    unknown.sort(key=lambda x: x[0])
    no_microconcept.sort(key=lambda x: x.id)

    at_risk_items = [i for (_score, _id, i) in at_risk]
    in_progress_items = [i for (_score, _id, i) in in_progress]

    # Interleave at_risk and in_progress to avoid bias towards a single bucket.
    interleaved: list[Item] = []
    a_idx = 0
    p_idx = 0
    while a_idx < len(at_risk_items) or p_idx < len(in_progress_items):
        for _ in range(AT_RISK_PER_CYCLE):
            if a_idx >= len(at_risk_items):
                break
            interleaved.append(at_risk_items[a_idx])
            a_idx += 1
        for _ in range(IN_PROGRESS_PER_CYCLE):
            if p_idx >= len(in_progress_items):
                break
            interleaved.append(in_progress_items[p_idx])
            p_idx += 1

        # If one bucket is exhausted, keep draining the other.
        if a_idx >= len(at_risk_items):
            interleaved.extend(in_progress_items[p_idx:])
            break
        if p_idx >= len(in_progress_items):
            interleaved.extend(at_risk_items[a_idx:])
            break

    ordered = interleaved
    ordered.extend([i for (_score, _id, i) in dominant])
    ordered.extend([i for (_id, i) in unknown])
    ordered.extend(no_microconcept)
    return ordered


def _select_prerequisite_microconcepts_v2(
    db: Session,
    *,
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    mastery_by_microconcept: dict[uuid.UUID, MasteryState],
    candidate_microconcept_ids: set[uuid.UUID],
) -> list[uuid.UUID]:
    targets = [
        ms
        for ms in mastery_by_microconcept.values()
        if ms.status == "at_risk" and ms.last_practice_at is not None
    ]
    if not targets:
        return []

    target_ids = [ms.microconcept_id for ms in targets]

    prereq_rows = (
        db.query(
            MicroConceptPrerequisite.microconcept_id,
            MicroConceptPrerequisite.prerequisite_microconcept_id,
        )
        .join(
            MicroConcept,
            MicroConcept.id == MicroConceptPrerequisite.prerequisite_microconcept_id,
        )
        .filter(
            MicroConceptPrerequisite.microconcept_id.in_(target_ids),
            MicroConcept.subject_id == subject_id,
            MicroConcept.term_id == term_id,
            MicroConcept.active == True,  # noqa: E712
        )
        .all()
    )
    if not prereq_rows:
        return []

    prereq_ids = {
        prereq_id
        for (_mcid, prereq_id) in prereq_rows
        if prereq_id in candidate_microconcept_ids and prereq_id not in target_ids
    }
    if not prereq_ids:
        return []

    scored: list[tuple[float, uuid.UUID]] = []
    for prereq_id in prereq_ids:
        ms = mastery_by_microconcept.get(prereq_id)
        if not ms:
            continue
        score = _to_float(ms.mastery_score)
        if score >= 0.8:
            continue
        scored.append((score, prereq_id))

    scored.sort(key=lambda t: (t[0], t[1]))
    return [prereq_id for (_score, prereq_id) in scored[:MAX_PREREQ_MICROCONCEPTS]]


def _adaptive_order_items_v2(
    db: Session,
    *,
    items: list[Item],
    mastery_by_microconcept: dict[uuid.UUID, MasteryState],
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
    candidate_microconcept_ids: set[uuid.UUID],
) -> list[Item]:
    prereq_microconcept_ids = set(
        _select_prerequisite_microconcepts_v2(
            db,
            student_id=student_id,
            subject_id=subject_id,
            term_id=term_id,
            mastery_by_microconcept=mastery_by_microconcept,
            candidate_microconcept_ids=candidate_microconcept_ids,
        )
    )

    if not prereq_microconcept_ids:
        return _adaptive_order_items_v1(items, mastery_by_microconcept)

    at_risk: list[tuple[float, uuid.UUID, Item]] = []
    prereq: list[tuple[float, uuid.UUID, Item]] = []
    in_progress: list[tuple[float, uuid.UUID, Item]] = []
    dominant: list[tuple[float, uuid.UUID, Item]] = []
    unknown: list[tuple[uuid.UUID, Item]] = []
    no_microconcept: list[Item] = []

    for item in items:
        if not item.microconcept_id:
            no_microconcept.append(item)
            continue

        ms = mastery_by_microconcept.get(item.microconcept_id)
        if not ms:
            unknown.append((item.id, item))
            continue

        score = _to_float(ms.mastery_score)
        key = (score, item.id, item)
        if ms.status == "at_risk":
            at_risk.append(key)
        elif item.microconcept_id in prereq_microconcept_ids:
            prereq.append(key)
        elif ms.status == "in_progress":
            in_progress.append(key)
        elif ms.status == "dominant":
            dominant.append(key)
        else:
            unknown.append((item.id, item))

    at_risk.sort(key=lambda x: (x[0], x[1]))
    prereq.sort(key=lambda x: (x[0], x[1]))
    in_progress.sort(key=lambda x: (x[0], x[1]))
    dominant.sort(key=lambda x: (x[0], x[1]))
    unknown.sort(key=lambda x: x[0])
    no_microconcept.sort(key=lambda x: x.id)

    at_risk_items = [i for (_score, _id, i) in at_risk]
    prereq_items = [i for (_score, _id, i) in prereq]
    in_progress_items = [i for (_score, _id, i) in in_progress]

    interleaved: list[Item] = []
    a_idx = 0
    r_idx = 0
    p_idx = 0

    while a_idx < len(at_risk_items) or r_idx < len(prereq_items) or p_idx < len(in_progress_items):
        for _ in range(AT_RISK_PER_CYCLE):
            if a_idx >= len(at_risk_items):
                break
            interleaved.append(at_risk_items[a_idx])
            a_idx += 1

        for _ in range(PREREQ_PER_CYCLE):
            if r_idx >= len(prereq_items):
                break
            interleaved.append(prereq_items[r_idx])
            r_idx += 1

        for _ in range(IN_PROGRESS_PER_CYCLE):
            if p_idx >= len(in_progress_items):
                break
            interleaved.append(in_progress_items[p_idx])
            p_idx += 1

        if a_idx >= len(at_risk_items) and r_idx >= len(prereq_items):
            interleaved.extend(in_progress_items[p_idx:])
            break
        if a_idx >= len(at_risk_items) and p_idx >= len(in_progress_items):
            interleaved.extend(prereq_items[r_idx:])
            break
        if r_idx >= len(prereq_items) and p_idx >= len(in_progress_items):
            interleaved.extend(at_risk_items[a_idx:])
            break

    ordered = interleaved
    ordered.extend([i for (_score, _id, i) in dominant])
    ordered.extend([i for (_id, i) in unknown])
    ordered.extend(no_microconcept)
    return ordered


def _apply_microconcept_cap(
    ordered_items: list[Item], *, item_count: int, max_per_microconcept: int
) -> list[Item]:
    selected: list[Item] = []
    skipped_due_to_cap: list[Item] = []
    counts: dict[uuid.UUID, int] = {}

    for item in ordered_items:
        if len(selected) >= item_count:
            break

        mcid = item.microconcept_id
        if mcid and counts.get(mcid, 0) >= max_per_microconcept:
            skipped_due_to_cap.append(item)
            continue

        selected.append(item)
        if mcid:
            counts[mcid] = counts.get(mcid, 0) + 1

    if len(selected) >= item_count:
        return selected

    # Soft fallback: fill remaining ignoring the cap if we can't reach item_count.
    for item in skipped_due_to_cap:
        if len(selected) >= item_count:
            break
        if item in selected:
            continue
        selected.append(item)

    return selected


@router.get("/activity-types", response_model=list[ActivityTypeResponse])
def list_activity_types(db: Session = Depends(get_db)):
    """
    List all activity types.
    """
    types = db.query(ActivityType).filter_by(active=True).all()
    return types


@router.post("/sessions", response_model=ActivitySessionResponse)
def create_session(
    session_data: ActivitySessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new activity session with randomly selected items.
    """
    role_name = get_current_role_name(db, current_user)
    if role_name == "student":
        student = get_current_student(db=db, current_user=current_user)
        if session_data.student_id != student.id:
            raise HTTPException(status_code=403, detail="Student mismatch")
        if student.subject_id and session_data.subject_id != student.subject_id:
            raise HTTPException(status_code=403, detail="Subject mismatch")
    elif role_name == "tutor":
        tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
        if not tutor:
            raise HTTPException(status_code=404, detail="Tutor not found")
        subject = db.get(Subject, session_data.subject_id)
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        if subject.tutor_id and subject.tutor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Subject not owned by tutor")
        student = db.get(Student, session_data.student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        if student.subject_id and student.subject_id != subject.id:
            raise HTTPException(status_code=403, detail="Student not in subject")
    else:
        raise HTTPException(status_code=403, detail="Role not allowed")

    # Get activity type
    activity_type = db.query(ActivityType).filter_by(id=session_data.activity_type_id).first()
    if not activity_type:
        raise HTTPException(status_code=404, detail="Activity type not found")

    allowed_item_types: list[ItemType]
    if activity_type.code == "MATCH":
        allowed_item_types = [ItemType.MATCH]
    elif activity_type.code == "CLOZE":
        allowed_item_types = [ItemType.CLOZE]
    else:
        # Default: QUIZ-like items
        allowed_item_types = [ItemType.MCQ, ItemType.TRUE_FALSE]

    # Select items for this session (adaptive V1)
    from app.models.content import ContentUpload

    base_query = (
        db.query(Item)
        .join(ContentUpload, Item.content_upload_id == ContentUpload.id)
        .filter(
            Item.is_active.is_(True),
            Item.type.in_(allowed_item_types),
            ContentUpload.subject_id == session_data.subject_id,
            ContentUpload.term_id == session_data.term_id,
        )
        .order_by(Item.id)
    )
    if session_data.content_upload_id:
        base_query = base_query.filter(ContentUpload.id == session_data.content_upload_id)

    candidate_items = base_query.all()
    if not candidate_items:
        raise HTTPException(status_code=404, detail="No items found for this subject/term")

    microconcept_ids = {i.microconcept_id for i in candidate_items if i.microconcept_id}
    mastery_by_microconcept = _fetch_mastery_map(
        db, student_id=session_data.student_id, microconcept_ids=microconcept_ids
    )

    ordered_items = _adaptive_order_items_v2(
        db,
        items=candidate_items,
        mastery_by_microconcept=mastery_by_microconcept,
        student_id=session_data.student_id,
        subject_id=session_data.subject_id,
        term_id=session_data.term_id,
        candidate_microconcept_ids=microconcept_ids,
    )
    selected_items = _apply_microconcept_cap(
        ordered_items,
        item_count=session_data.item_count,
        max_per_microconcept=MAX_ITEMS_PER_MICROCONCEPT,
    )
    selected_items = selected_items[: session_data.item_count]

    # Create session
    session = ActivitySession(
        id=uuid.uuid4(),
        student_id=session_data.student_id,
        activity_type_id=session_data.activity_type_id,
        subject_id=session_data.subject_id,
        term_id=session_data.term_id,
        topic_id=session_data.topic_id,
        started_at=datetime.utcnow(),
        status="in_progress",
        device_type=session_data.device_type,
    )
    db.add(session)
    db.flush()

    # Create session items
    for idx, item in enumerate(selected_items):
        session_item = ActivitySessionItem(
            id=uuid.uuid4(),
            session_id=session.id,
            item_id=item.id,
            order_index=idx,
            presented_at=datetime.utcnow() if idx == 0 else None,
        )
        db.add(session_item)

    db.commit()
    db.refresh(session)

    return session


@router.get("/sessions/{session_id}", response_model=ActivitySessionResponse)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get an activity session by ID.
    """
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    role_name = get_current_role_name(db, current_user)
    if role_name == "student":
        student = get_current_student(db=db, current_user=current_user)
        if session.student_id != student.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    elif role_name == "tutor":
        subject = db.get(Subject, session.subject_id)
        if subject and subject.tutor_id and subject.tutor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    else:
        raise HTTPException(status_code=403, detail="Role not allowed")

    return session


@router.get("/sessions/{session_id}/items", response_model=list[ItemResponse])
def get_session_items(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    role_name = get_current_role_name(db, current_user)
    if role_name == "student":
        student = get_current_student(db=db, current_user=current_user)
        if session.student_id != student.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    elif role_name == "tutor":
        subject = db.get(Subject, session.subject_id)
        if subject and subject.tutor_id and subject.tutor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    else:
        raise HTTPException(status_code=403, detail="Role not allowed")

    items = (
        db.query(Item)
        .join(ActivitySessionItem, ActivitySessionItem.item_id == Item.id)
        .filter(
            ActivitySessionItem.session_id == session_id,
            Item.is_active.is_(True),
        )
        .order_by(ActivitySessionItem.order_index.asc())
        .all()
    )
    return items


def _compute_match_correct(item: Item, response_normalized: str | None) -> bool:
    if not response_normalized:
        return False
    if not item.options or not isinstance(item.options, dict):
        return False
    pairs = item.options.get("pairs")
    if not isinstance(pairs, list):
        return False

    expected: dict[str, str] = {}
    for pair in pairs:
        if not isinstance(pair, dict):
            continue
        left = pair.get("left")
        right = pair.get("right")
        if isinstance(left, str) and isinstance(right, str):
            expected[left] = right

    if not expected:
        return False

    try:
        submitted = json.loads(response_normalized)
    except json.JSONDecodeError:
        return False
    if not isinstance(submitted, dict):
        return False

    normalized_submitted: dict[str, str] = {}
    for key, value in submitted.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized_submitted[key] = value

    return normalized_submitted == expected


def _normalize_text(text: str) -> str:
    # Normalize (case/whitespace/diacritics) for tolerant comparisons.
    decomposed = normalize("NFKD", text)
    without_diacritics = "".join(ch for ch in decomposed if not combining(ch))
    collapsed = " ".join(without_diacritics.strip().split())
    return collapsed.casefold()


def _compute_cloze_correct(item: Item, response_normalized: str | None) -> bool:
    if not response_normalized:
        return False

    submitted = _normalize_text(response_normalized)
    if not submitted:
        return False

    # Allow multiple acceptable answers stored as JSON array in correct_answer.
    acceptable: list[str] = []
    try:
        parsed = json.loads(item.correct_answer)
        if isinstance(parsed, list):
            acceptable = [str(x) for x in parsed if isinstance(x, (str, int, float))]
    except json.JSONDecodeError:
        acceptable = []

    if not acceptable:
        acceptable = [item.correct_answer]

    return any(_normalize_text(ans) == submitted for ans in acceptable if isinstance(ans, str))


def _compute_quiz_correct(item: Item, response_normalized: str | None) -> bool:
    if not response_normalized:
        return False
    return _normalize_text(response_normalized) == _normalize_text(item.correct_answer)


@router.post("/sessions/{session_id}/responses", response_model=LearningEventResponse)
def record_response(
    session_id: uuid.UUID,
    event_data: LearningEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record a student response as a learning event.
    """
    # Verify session exists
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    role_name = get_current_role_name(db, current_user)
    if role_name != "student":
        raise HTTPException(status_code=403, detail="Only students can submit responses")
    student = get_current_student(db=db, current_user=current_user)
    if event_data.student_id != student.id or session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Student mismatch")

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")

    # Get item to derive microconcept_id if not provided
    item = db.query(Item).filter_by(id=event_data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.is_active:
        raise HTTPException(status_code=400, detail="Item is not active")

    is_correct = event_data.is_correct
    if item.type == ItemType.MATCH:
        is_correct = _compute_match_correct(item, event_data.response_normalized)
    elif item.type == ItemType.CLOZE:
        is_correct = _compute_cloze_correct(item, event_data.response_normalized)
    elif item.type in (ItemType.MCQ, ItemType.TRUE_FALSE):
        is_correct = _compute_quiz_correct(item, event_data.response_normalized)

    # Create learning event
    event = LearningEvent(
        id=uuid.uuid4(),
        student_id=event_data.student_id,
        session_id=session_id,
        subject_id=event_data.subject_id,
        term_id=event_data.term_id,
        topic_id=event_data.topic_id,
        microconcept_id=event_data.microconcept_id or item.microconcept_id,
        activity_type_id=event_data.activity_type_id,
        item_id=event_data.item_id,
        timestamp_start=event_data.timestamp_start,
        timestamp_end=event_data.timestamp_end,
        duration_ms=event_data.duration_ms,
        attempt_number=event_data.attempt_number,
        response_normalized=event_data.response_normalized,
        is_correct=is_correct,
        hint_used=event_data.hint_used,
        difficulty_at_time=event_data.difficulty_at_time,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.post("/sessions/{session_id}/end", response_model=ActivitySessionResponse)
def end_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    End an activity session and trigger metrics recalculation.
    """
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    role_name = get_current_role_name(db, current_user)
    if role_name != "student":
        raise HTTPException(status_code=403, detail="Only students can end sessions")
    student = get_current_student(db=db, current_user=current_user)
    if session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session already ended")

    # Update session
    session.ended_at = datetime.utcnow()
    session.status = "completed"
    db.commit()
    db.refresh(session)

    # Trigger metrics recalculation (async in production, sync for MVP)
    try:
        metric_service.recalculate_and_save_metrics(
            db, session.student_id, session.subject_id, session.term_id
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error recalculating metrics: {e}")

    return session


@router.post("/sessions/{session_id}/feedback")
def submit_session_feedback(
    session_id: uuid.UUID,
    feedback: ActivitySessionFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    role_name = get_current_role_name(db, current_user)
    if role_name != "student":
        raise HTTPException(status_code=403, detail="Only students can submit feedback")

    student = get_current_student(db=db, current_user=current_user)
    session = db.query(ActivitySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Session must be completed before feedback")

    session.feedback_rating = feedback.rating
    session.feedback_text = feedback.text
    session.feedback_submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(session)
    return {"message": "Feedback saved", "session_id": session_id}
