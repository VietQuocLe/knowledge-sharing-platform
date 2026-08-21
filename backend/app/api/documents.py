from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import ResourceType
from app.schemas.document import AssetDownloadResponse, DocumentPageResponse, DocumentResponse
from app.services.document_service import (
    PRESIGNED_URL_EXPIRES_SECONDS,
    get_all,
    get_asset_download_url,
    get_by_id,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=DocumentPageResponse)
def list_documents(
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
    return DocumentPageResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{document_id:int}", response_model=DocumentResponse)
def read_document(document_id: int, db: Session = Depends(get_db)):
    return get_by_id(db, document_id)


@router.get(
    "/{document_id:int}/assets/{asset_id:int}/download",
    response_model=AssetDownloadResponse,
)
def download_document_asset(
    document_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
):
    download_url, file_name = get_asset_download_url(db, document_id, asset_id)
    return AssetDownloadResponse(
        download_url=download_url,
        file_name=file_name,
        expires_in_seconds=PRESIGNED_URL_EXPIRES_SECONDS,
    )
