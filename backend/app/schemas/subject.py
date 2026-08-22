from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SubjectCategory
from app.schemas.major import MajorResponse


class SubjectBase(BaseModel):
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(SubjectBase):
    department_id: int
    major_ids: list[int]


class SubjectUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    department_id: int
    major_ids: list[int]


class SubjectResponse(SubjectBase):
    id: int
    majors: list[MajorResponse] = Field(default_factory=list)
    category: Optional[SubjectCategory] = None

    model_config = ConfigDict(from_attributes=True)