from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


LEAVE_TYPE_PATTERN = r"^(ANNUAL|SICK|UNPAID|OTHER)$"


class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: str = Field(pattern=LEAVE_TYPE_PATTERN)
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu")
        return self


class LeaveDecisionRequest(BaseModel):
    status: str = Field(pattern=r"^(APPROVED|REJECTED)$")
    note: str | None = Field(default=None, max_length=500)


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    full_name: str
    leave_type: str
    start_date: date
    end_date: date
    total_days: int
    reason: str
    status: str
    created_by: str
    decided_at: datetime | None
    decision_note: str | None
    created_at: datetime


class LeaveDecisionResponse(BaseModel):
    leave: LeaveRequestResponse
    applied_days: int
    skipped_days: int
