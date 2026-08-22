from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotebookBase(BaseModel):
    title: str
    subject_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class NotebookCreate(NotebookBase):
    pass


class NotebookRead(NotebookBase):
    id: int
    subject_name: str | None = None
    source_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
