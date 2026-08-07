from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_admin
from app.core.database import get_db
from app.models.enums import ResourceType
from app.models.user import User
from app.schemas.resource import (
    ResourceCreate,
    ResourcePageResponse,
    ResourceResponse,
    ResourceUpdate,
)
from app.services.resource_service import create, delete, get_all, get_by_id, update

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/", response_model=ResourcePageResponse)
def list_resources(
    subject_id: int | None = Query(default=None),
    resource_type: ResourceType | None = Query(default=None),
    page: int = Query(default=1),
    size: int = Query(default=20),
    db: Session = Depends(get_db),
):
    items, total = get_all(
        db,
        subject_id=subject_id,
        resource_type=resource_type,
        page=page,
        size=size,
    )
    return ResourcePageResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{resource_id}", response_model=ResourceResponse)
def read_resource(resource_id: int, db: Session = Depends(get_db)):
    return get_by_id(db, resource_id)


@router.post("/", response_model=ResourceResponse, status_code=201)
def create_resource(
    data: ResourceCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create(db, data, current_user)


@router.put("/{resource_id}", response_model=ResourceResponse, dependencies=[Depends(get_current_admin)])
def update_resource(resource_id: int, data: ResourceUpdate, db: Session = Depends(get_db)):
    return update(db, resource_id, data)


@router.delete("/{resource_id}", dependencies=[Depends(get_current_admin)], status_code=204)
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    delete(db, resource_id)