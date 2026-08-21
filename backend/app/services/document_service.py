from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.asset import Asset
from app.models.document import Document
from app.models.enums import DocumentStatus, ResourceType
from app.models.subject import Subject
from app.services import storage_service

PRESIGNED_URL_EXPIRES_SECONDS = 900


def _public_document_filters(
    *,
    subject_id: int | None = None,
    resource_type: ResourceType | None = None,
) -> list:
    filters = [Document.status == DocumentStatus.PUBLIC]
    if subject_id is not None:
        filters.append(Document.subject_id == subject_id)
    if resource_type is not None:
        filters.append(Document.resource_type == resource_type)
    return filters


def _get_subject_or_404(db: Session, subject_id: int) -> Subject:
    subject = db.execute(select(Subject).where(Subject.id == subject_id)).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


def _validate_pagination(*, page: int, size: int) -> None:
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page must be greater than 0")
    if size < 1 or size > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="size must be between 1 and 100")


def get_all(
    db: Session,
    *,
    subject_id: int | None = None,
    resource_type: ResourceType | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Document], int]:
    _validate_pagination(page=page, size=size)

    if subject_id is not None:
        _get_subject_or_404(db, subject_id)

    filters = _public_document_filters(subject_id=subject_id, resource_type=resource_type)

    total = db.execute(select(func.count()).select_from(Document).where(*filters)).scalar_one()

    result = db.execute(
        select(Document)
        .options(selectinload(Document.assets))
        .where(*filters)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.scalars().all()), total


def get_by_id(db: Session, document_id: int) -> Document:
    document = db.execute(
        select(Document)
        .options(selectinload(Document.assets))
        .where(
            Document.id == document_id,
            Document.status == DocumentStatus.PUBLIC,
        )
    ).scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


def get_asset_download_url(db: Session, document_id: int, asset_id: int) -> tuple[str, str]:
    document = get_by_id(db, document_id)

    asset = db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.document_id == document.id,
        )
    ).scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    download_url = storage_service.get_presigned_download_url(
        object_path=asset.file_path,
        expires_seconds=PRESIGNED_URL_EXPIRES_SECONDS,
    )
    return download_url, asset.file_name
