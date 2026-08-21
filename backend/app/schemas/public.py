from datetime import date, datetime

from pydantic import BaseModel, Field


class PublicLookupRequest(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    national_id: str = Field(min_length=1, max_length=20)
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)


class PublicAttendanceDay(BaseModel):
    work_date: date
    check_in: datetime | None
    check_out: datetime | None
    worked_minutes: int
    late_minutes: int
    overtime_minutes: int
    status: str


class PublicAttendanceSummary(BaseModel):
    present_days: int
    leave_days: int
    late_days: int
    total_worked_minutes: int
    approved_overtime_minutes: int


class PublicAttendanceResponse(BaseModel):
    employee_code: str
    full_name: str
    department: str | None
    shift_code: str | None
    year: int
    month: int
    summary: PublicAttendanceSummary
    days: list[PublicAttendanceDay]
