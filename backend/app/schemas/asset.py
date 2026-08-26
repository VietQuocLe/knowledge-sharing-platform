from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from app.models.enums import AssetConversionStatus


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
