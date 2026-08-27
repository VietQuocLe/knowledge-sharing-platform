from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator


class NotebookChatMessageBase(BaseModel):
    role: str
    content: str
    citations: Any | None = None
    condensed_query: str | None = None

    model_config = ConfigDict(from_attributes=True)


class NotebookChatMessageCreate(NotebookChatMessageBase):
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("Role must be 'user' or 'assistant'")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class NotebookChatMessageRead(NotebookChatMessageBase):
    id: int
    session_id: int
    created_at: datetime


class NotebookChatSessionBase(BaseModel):
    title: str

    model_config = ConfigDict(from_attributes=True)


class NotebookChatSessionCreate(BaseModel):
    title: str | None = "Phiên trò chuyện mới"

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Any) -> str | None:
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("Title must be a string")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty")
        if len(trimmed) > 500:
            raise ValueError("Title cannot exceed 500 characters")
        return trimmed


class NotebookChatSessionUpdate(BaseModel):
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


class NotebookChatSessionRead(NotebookChatSessionBase):
    id: int
    notebook_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class NotebookChatSessionDetailRead(NotebookChatSessionRead):
    messages: list[NotebookChatMessageRead]
