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
