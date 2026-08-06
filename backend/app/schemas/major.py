from pydantic import BaseModel, ConfigDict

from app.schemas.department import DepartmentBase


class MajorBase(BaseModel):
    code: str
    name: str
    department_id: int

    model_config = ConfigDict(from_attributes=True)


class MajorCreate(BaseModel):
    code: str
    name: str
    department_id: int


class MajorUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    department_id: int | None = None


class MajorResponse(MajorBase):
    id: int
    department: DepartmentBase | None = None

    model_config = ConfigDict(from_attributes=True)