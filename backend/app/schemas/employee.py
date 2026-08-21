from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeBase(BaseModel):
    employee_code: str = Field(
        min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$"
    )
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None, max_length=30, pattern=r"^$|^[0-9+\-\s]{8,30}$"
    )
    # CCCD is 12 digits; the older CMND is 9. Both are accepted.
    national_id: str | None = Field(
        default=None, max_length=20, pattern=r"^$|^[0-9]{9,12}$"
    )
    department_id: int | None = None
    shift_id: int


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    status: str = Field(pattern=r"^(ACTIVE|INACTIVE|PENDING_ENROLLMENT)$")


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department: str | None = None
    status: str
    enrollment_status: str
    sample_count: int
    has_centroid: bool
    created_at: datetime
    updated_at: datetime
