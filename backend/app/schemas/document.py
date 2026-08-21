from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus, ResourceType
from app.schemas.asset import AssetResponse


class DocumentBase(BaseModel):
    title: str
    description: str | None = None
    subject_id: int
    resource_type: ResourceType

    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(DocumentBase):
    status: DocumentStatus = DocumentStatus.PUBLIC


class DocumentResponse(DocumentBase):
    id: int
    created_by: int
    status: DocumentStatus
    created_at: datetime
    assets: list[AssetResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DocumentPageResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)


class AssetDownloadResponse(BaseModel):
    download_url: str
    file_name: str
    expires_in_seconds: int

    model_config = ConfigDict(from_attributes=True)
