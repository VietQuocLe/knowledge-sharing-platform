from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator


class NotebookBase(BaseModel):
    title: str
    subject_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Title must be a string")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty")
        if len(trimmed) > 500:
            raise ValueError("Title cannot exceed 500 characters")
        return trimmed


class NotebookCreate(NotebookBase):
    pass


class NotebookUpdate(BaseModel):
    title: str

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Title must be a string")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty")
        if len(trimmed) > 500:
            raise ValueError("Title cannot exceed 500 characters")
        return trimmed


class NotebookRead(NotebookBase):
    id: int
    subject_name: str | None = None
    source_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotebookSourceRead(BaseModel):
    id: int
    type: str  # "local" | "saved"
    title: str
    file_type: str
    size: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotebookDetailRead(BaseModel):
    id: int
    title: str
    subject_id: int | None = None
    subject_name: str | None = None
    sources_count: int
    max_sources: int
    sources: list[NotebookSourceRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotebookSavedDocumentCreate(BaseModel):
    document_id: int


class NotebookSavedDocumentRead(BaseModel):
    notebook_id: int
    document_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

