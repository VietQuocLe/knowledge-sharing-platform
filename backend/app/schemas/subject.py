from pydantic import BaseModel, ConfigDict, Field

from app.schemas.major import MajorBase


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
    majors: list[MajorBase] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)