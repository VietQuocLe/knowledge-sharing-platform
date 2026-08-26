from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from app.models.enums import AssetConversionStatus, AssetIngestionStatus


class AssetBase(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    size: int

    model_config = ConfigDict(from_attributes=True)


class AssetCreate(AssetBase):
    document_id: int | None = None
    notebook_id: int | None = None


class AssetResponse(AssetBase):
    id: int
    document_id: int | None = None
    notebook_id: int | None = None
    converted_pdf_path: str | None = None
    conversion_status: AssetConversionStatus | None = None

    model_config = ConfigDict(from_attributes=True)


class AssetIngestionStatusResponse(BaseModel):
    asset_id: int
    file_name: str
    ingestion_status: AssetIngestionStatus
    chunk_count: int
    ingestion_error: str | None = None

    model_config = ConfigDict(from_attributes=True)
