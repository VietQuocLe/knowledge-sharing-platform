from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)
