from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.enums import ResourceType, VisibilityEnum
from app.models.user import User
from app.schemas.resource import (
    ResourceCreate,
    ResourcePageResponse,
    ResourceRejectRequest,
    ResourceResponse,
    ResourceUpdate,
)
from app.services.resource_service import (
    approve_for_public,
    create,
    delete,
    get_all,
    get_for_admin,
    get_by_id,
    get_owned,
    get_owned_by_id,
    reject_resource,
    submit_for_review,
    update,
    upload_asset,
)

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


@router.get("/me", response_model=ResourcePageResponse)
def list_my_resources(
    subject_id: int | None = Query(default=None),
    resource_type: ResourceType | None = Query(default=None),
    page: int = Query(default=1),
    size: int = Query(default=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = get_owned(
        db,
        current_user,
        subject_id=subject_id,
        resource_type=resource_type,
        page=page,
        size=size,
    )
    return ResourcePageResponse(items=items, total=total, page=page, size=size)


@router.get("/me/{resource_id:int}", response_model=ResourceResponse)
def read_my_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_owned_by_id(db, resource_id, current_user)


@router.get("/admin", response_model=ResourcePageResponse, dependencies=[Depends(require_admin)])
def list_resources_for_admin(
    visibility: VisibilityEnum | None = Query(default=None),
    page: int = Query(default=1),
    size: int = Query(default=100),
    db: Session = Depends(get_db),
):
    items, total = get_for_admin(db, visibility=visibility, page=page, size=size)
    return ResourcePageResponse(items=items, total=total, page=page, size=size)


@router.get("/{resource_id:int}", response_model=ResourceResponse)
def read_resource(resource_id: int, db: Session = Depends(get_db)):
    return get_by_id(db, resource_id)


@router.post("/", response_model=ResourceResponse, status_code=201)
def create_resource(
    data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create(db, data, current_user)


@router.post("/{resource_id:int}/assets", response_model=ResourceResponse, status_code=201)
def upload_resource_asset(
    resource_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upload_asset(db, resource_id, current_user, file)


@router.post("/{resource_id:int}/submit-review", response_model=ResourceResponse)
def submit_resource_for_review(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return submit_for_review(db, resource_id, current_user)


@router.post("/{resource_id:int}/approve", response_model=ResourceResponse, dependencies=[Depends(require_admin)])
def approve_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return approve_for_public(db, resource_id, current_user)


@router.post("/{resource_id:int}/reject", response_model=ResourceResponse, dependencies=[Depends(require_admin)])
def reject_resource_endpoint(
    resource_id: int,
    data: ResourceRejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return reject_resource(db, resource_id, current_user, data.reason)


@router.put("/{resource_id:int}", response_model=ResourceResponse, dependencies=[Depends(require_admin)])
def update_resource(resource_id: int, data: ResourceUpdate, db: Session = Depends(get_db)):
    return update(db, resource_id, data)


@router.delete("/{resource_id:int}", dependencies=[Depends(require_admin)], status_code=204)
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    delete(db, resource_id)
