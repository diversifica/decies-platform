import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_admin
from app.models.activity import ActivityType
from app.models.item import Item
from app.models.recommendation_catalog import RecommendationCatalog
from app.models.user import User
from app.schemas.activity import ActivityTypeResponse
from app.schemas.admin import (
    AdminActivityTypeUpdate,
    AdminItemSummary,
    AdminRecommendationCatalogResponse,
    AdminRecommendationCatalogUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/items", response_model=list[AdminItemSummary])
def list_items(
    limit: int = 50,
    offset: int = 0,
    content_upload_id: uuid.UUID | None = None,
    microconcept_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    query = db.query(Item)
    if content_upload_id:
        query = query.filter(Item.content_upload_id == content_upload_id)
    if microconcept_id:
        query = query.filter(Item.microconcept_id == microconcept_id)
    if is_active is not None:
        query = query.filter(Item.is_active == is_active)
    return query.order_by(Item.created_at.desc().nullslast()).offset(offset).limit(limit).all()


@router.get("/recommendation-catalog", response_model=list[AdminRecommendationCatalogResponse])
def list_recommendation_catalog(
    active: bool | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    query = db.query(RecommendationCatalog)
    if active is not None:
        query = query.filter(RecommendationCatalog.active == active)
    if category:
        query = query.filter(RecommendationCatalog.category == category)
    return query.order_by(RecommendationCatalog.code).all()


@router.patch(
    "/recommendation-catalog/{code}",
    response_model=AdminRecommendationCatalogResponse,
)
def update_recommendation_catalog(
    code: str,
    payload: AdminRecommendationCatalogUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    row = db.query(RecommendationCatalog).filter(RecommendationCatalog.code == code).first()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation catalog entry not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/activity-types", response_model=list[ActivityTypeResponse])
def list_activity_types(
    active: bool | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    query = db.query(ActivityType)
    if active is not None:
        query = query.filter(ActivityType.active == active)
    return query.order_by(ActivityType.code).all()


@router.patch("/activity-types/{activity_type_id}", response_model=ActivityTypeResponse)
def update_activity_type(
    activity_type_id: uuid.UUID,
    payload: AdminActivityTypeUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    row = db.get(ActivityType, activity_type_id)
    if not row:
        raise HTTPException(status_code=404, detail="Activity type not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
