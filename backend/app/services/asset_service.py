from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.schemas.asset import AssetCreate


def validate_asset_parent(*, document_id: int | None, notebook_id: int | None) -> None:
    has_document = document_id is not None
    has_notebook = notebook_id is not None

    if has_document and has_notebook:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset cannot belong to both a document and a notebook",
        )

    if not has_document and not has_notebook:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset must belong to either a document or a notebook",
        )


def create(db: Session, data: AssetCreate) -> Asset:
    validate_asset_parent(document_id=data.document_id, notebook_id=data.notebook_id)

    asset = Asset(
        document_id=data.document_id,
        notebook_id=data.notebook_id,
        file_name=data.file_name,
        file_path=data.file_path,
        file_type=data.file_type,
        size=data.size,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
