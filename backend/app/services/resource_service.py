from __future__ import annotations

import io
import logging
import re
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.enums import ResourceStatus, ResourceType, UserRole, VisibilityEnum
from app.models.resource import Asset, Resource
from app.models.subject import Subject
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceUpdate
from app.services import storage_service

logger = logging.getLogger(__name__)


def _get_subject_or_404(db: Session, subject_id: int) -> Subject:
    subject = db.execute(select(Subject).where(Subject.id == subject_id)).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


def _get_resource_or_404(
    db: Session,
    resource_id: int,
    *,
    include_deleted: bool = False,
    public_only: bool = False,
) -> Resource:
    query = select(Resource).options(selectinload(Resource.assets)).where(Resource.id == resource_id)
    if not include_deleted:
        query = query.where(Resource.status != ResourceStatus.DELETED)
    if public_only:
        query = query.where(Resource.visibility == VisibilityEnum.PUBLIC)

    resource = db.execute(query).scalar_one_or_none()
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


def _get_manageable_resource_or_403(db: Session, resource_id: int, current_user: User) -> Resource:
    resource = _get_resource_or_404(db, resource_id, include_deleted=True)
    if current_user.role != UserRole.ADMIN and resource.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    if resource.status == ResourceStatus.DELETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource is deleted")
    return resource


def _normalize_filename(filename: str) -> str:
    base_name = Path(filename).name.strip() or "upload"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base_name)


def _detect_file_type(filename: str, file_bytes: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and DOCX files are allowed")

    if extension == ".pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF file")
        return "PDF"

    if not zipfile.is_zipfile(io.BytesIO(file_bytes)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid DOCX file")

    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
        names = set(archive.namelist())
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid DOCX file")

    return "DOCX"


def _ensure_allowed_file_type(detected_type: str) -> None:
    if detected_type not in settings.ALLOWED_UPLOAD_FILE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type is not allowed")


def _validate_upload_limits(db: Session, resource_id: int, file_size: int) -> None:
    max_file_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the limit of {settings.MAX_FILE_SIZE_MB} MB",
        )

    asset_count = db.execute(
        select(func.count()).select_from(Asset).where(Asset.resource_id == resource_id)
    ).scalar_one()
    if asset_count >= settings.MAX_ASSETS_PER_RESOURCE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Each resource can have at most {settings.MAX_ASSETS_PER_RESOURCE} assets",
        )


def _refresh_resource(db: Session, resource_id: int) -> Resource:
    return _get_resource_or_404(db, resource_id, include_deleted=True)


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

    filters = [
        Resource.subject_id == subject_id,
        Resource.visibility == VisibilityEnum.PUBLIC,
        Resource.status != ResourceStatus.DELETED,
    ]
    if resource_type is not None:
        filters.append(Resource.resource_type == resource_type)

    total = db.execute(select(func.count()).select_from(Resource).where(*filters)).scalar_one()

    result = db.execute(
        select(Resource)
        .options(selectinload(Resource.assets))
        .where(*filters)
        .order_by(Resource.created_at.desc(), Resource.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.scalars().all()), total


def get_owned(
    db: Session,
    current_user: User,
    *,
    subject_id: int | None = None,
    resource_type: ResourceType | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Resource], int]:
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page must be greater than 0")
    if size < 1 or size > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="size must be between 1 and 100")

    filters = [Resource.owner_id == current_user.id, Resource.status != ResourceStatus.DELETED]
    if subject_id is not None:
        filters.append(Resource.subject_id == subject_id)
    if resource_type is not None:
        filters.append(Resource.resource_type == resource_type)

    total = db.execute(select(func.count()).select_from(Resource).where(*filters)).scalar_one()

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
    return _get_resource_or_404(db, resource_id, public_only=True)


def create(db: Session, data: ResourceCreate, current_user: User) -> Resource:
    _get_subject_or_404(db, data.subject_id)

    visibility = data.visibility or VisibilityEnum.PRIVATE
    if visibility == VisibilityEnum.PUBLIC and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    resource = Resource(
        owner_id=current_user.id,
        subject_id=data.subject_id,
        title=data.title,
        description=data.description,
        resource_type=data.resource_type,
        visibility=visibility,
        metadata_json=data.metadata_json,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return _get_resource_or_404(db, resource.id, include_deleted=True)


def upload_asset(db: Session, resource_id: int, current_user: User, upload_file: UploadFile) -> Resource:
    _get_manageable_resource_or_403(db, resource_id, current_user)

    file_bytes = upload_file.file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    _validate_upload_limits(db, resource_id, len(file_bytes))

    file_name = upload_file.filename or "upload"
    detected_type = _detect_file_type(file_name, file_bytes)
    _ensure_allowed_file_type(detected_type)

    clean_file_name = _normalize_filename(file_name)
    object_path = f"resources/{resource_id}/{uuid.uuid4().hex}_{clean_file_name}"

    storage_service.upload_object(
        object_path=object_path,
        data=file_bytes,
        content_type=upload_file.content_type or "application/octet-stream",
    )

    asset = Asset(
        resource_id=resource_id,
        file_name=clean_file_name,
        file_path=object_path,
        file_type=detected_type,
        size=len(file_bytes),
    )
    db.add(asset)

    try:
        db.commit()
    except Exception:
        db.rollback()
        try:
            storage_service.delete_object(object_path)
        except Exception:
            logger.exception("Failed to clean up uploaded object %s after DB error", object_path)
        raise

    return _refresh_resource(db, resource_id)


def submit_for_review(db: Session, resource_id: int, current_user: User) -> Resource:
    resource = _get_manageable_resource_or_403(db, resource_id, current_user)
    if resource.visibility != VisibilityEnum.PRIVATE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource must be private to submit for review")

    resource.visibility = VisibilityEnum.PENDING_REVIEW
    db.commit()
    db.refresh(resource)
    return _refresh_resource(db, resource_id)


def approve_for_public(db: Session, resource_id: int, current_user: User) -> Resource:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    resource = _get_resource_or_404(db, resource_id, include_deleted=True)
    if resource.status == ResourceStatus.DELETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource is deleted")
    if resource.visibility != VisibilityEnum.PENDING_REVIEW:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource must be pending review to approve")

    resource.visibility = VisibilityEnum.PUBLIC
    db.commit()
    db.refresh(resource)
    return _refresh_resource(db, resource_id)


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