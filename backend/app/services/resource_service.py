from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import ResourceStatus, ResourceType
from app.models.resource import Resource
from app.models.subject import Subject
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceUpdate


def _get_subject_or_404(db: Session, subject_id: int) -> Subject:
    subject = db.execute(
        select(Subject).where(Subject.id == subject_id)
    ).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


def _get_resource_or_404(
    db: Session,
    resource_id: int,
    *,
    include_deleted: bool = False,
) -> Resource:
    query = select(Resource).options(selectinload(Resource.assets)).where(Resource.id == resource_id)
    if not include_deleted:
        query = query.where(Resource.status != ResourceStatus.DELETED)

    resource = db.execute(query).scalar_one_or_none()
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


def get_all(
    db: Session,
    *,
    subject_id: int | None,
    resource_type: ResourceType | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Resource], int]:
    if subject_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="subject_id is required")
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page must be greater than 0")
    if size < 1 or size > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="size must be between 1 and 100")

    _get_subject_or_404(db, subject_id)

    filters = [Resource.subject_id == subject_id, Resource.status != ResourceStatus.DELETED]
    if resource_type is not None:
        filters.append(Resource.resource_type == resource_type)

    total = db.execute(
        select(func.count()).select_from(Resource).where(*filters)
    ).scalar_one()

    result = db.execute(
        select(Resource)
        .options(selectinload(Resource.assets))
        .where(*filters)
        .order_by(Resource.created_at.desc(), Resource.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.scalars().all()), total


def get_by_id(db: Session, resource_id: int) -> Resource:
    return _get_resource_or_404(db, resource_id)


def create(db: Session, data: ResourceCreate, current_user: User) -> Resource:
    _get_subject_or_404(db, data.subject_id)

    resource = Resource(
        owner_id=current_user.id,
        subject_id=data.subject_id,
        title=data.title,
        description=data.description,
        resource_type=data.resource_type,
        status=ResourceStatus.PUBLISHED,
        metadata_json=data.metadata_json,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return _get_resource_or_404(db, resource.id, include_deleted=True)


def update(db: Session, resource_id: int, data: ResourceUpdate) -> Resource:
    resource = _get_resource_or_404(db, resource_id, include_deleted=True)
    if resource.status == ResourceStatus.DELETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource is deleted")

    if data.subject_id is not None and data.subject_id != resource.subject_id:
        _get_subject_or_404(db, data.subject_id)
        resource.subject_id = data.subject_id

    if data.title is not None:
        resource.title = data.title

    if data.description is not None:
        resource.description = data.description

    if data.resource_type is not None:
        resource.resource_type = data.resource_type

    if data.metadata_json is not None:
        resource.metadata_json = data.metadata_json

    db.commit()
    db.refresh(resource)
    return _get_resource_or_404(db, resource_id, include_deleted=True)


def delete(db: Session, resource_id: int) -> None:
    resource = _get_resource_or_404(db, resource_id)
    resource.status = ResourceStatus.DELETED
    db.commit()