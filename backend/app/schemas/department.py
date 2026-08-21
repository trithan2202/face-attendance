from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    code: str = Field(
        min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$"
    )
    name: str = Field(min_length=1, max_length=255)
    manager_name: str | None = Field(default=None, max_length=255)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_count: int
    created_at: datetime
    updated_at: datetime
