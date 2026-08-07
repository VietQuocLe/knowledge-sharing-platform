from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ResourceStatus, ResourceType


class AssetBase(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    version: int
    size: int

    model_config = ConfigDict(from_attributes=True)


class AssetResponse(AssetBase):
    id: int
    resource_id: int

    model_config = ConfigDict(from_attributes=True)


class ResourceBase(BaseModel):
    title: str
    description: str | None = None
    resource_type: ResourceType
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ResourceCreate(ResourceBase):
    subject_id: int


class ResourceUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    resource_type: ResourceType | None = None
    metadata_json: dict[str, Any] | None = None
    subject_id: int | None = None


class ResourceResponse(ResourceBase):
    id: int
    owner_id: int
    subject_id: int | None
    status: ResourceStatus
    created_at: datetime
    assets: list[AssetResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResourcePageResponse(BaseModel):
    items: list[ResourceResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)