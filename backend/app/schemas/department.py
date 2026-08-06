from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None


class DepartmentResponse(DepartmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)