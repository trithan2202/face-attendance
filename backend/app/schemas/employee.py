from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeBase(BaseModel):
    employee_code: str = Field(
        min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$"
    )
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    department: str | None = Field(default=None, max_length=255)
    shift_id: int


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    status: str = Field(pattern=r"^(ACTIVE|INACTIVE|PENDING_ENROLLMENT)$")


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    enrollment_status: str
    sample_count: int
    has_centroid: bool
    created_at: datetime
    updated_at: datetime
