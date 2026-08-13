from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AttendanceDailyResponse(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    full_name: str
    department: str | None
    shift_id: int
    shift_code: str
    work_date: date
    first_check_in: datetime | None
    last_check_out: datetime | None
    worked_minutes: int
    late_minutes: int
    early_leave_minutes: int
    overtime_minutes: int
    status: str
    is_late: bool
    is_early_leave: bool
    is_overtime: bool


class AttendanceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    recognized_at: datetime
    similarity: float
    detection_score: float | None
    recognition_method: str


class AttendanceDetailResponse(BaseModel):
    daily: AttendanceDailyResponse
    events: list[AttendanceEventResponse]


class AttendanceAdjustmentRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    first_check_in: datetime | None = None
    last_check_out: datetime | None = None
    status: str | None = Field(
        default=None,
        pattern=r"^(PRESENT|MISSING_CHECK_IN|MISSING_CHECK_OUT|ABSENT)$",
    )

    @model_validator(mode="after")
    def has_change(self):
        fields = self.model_fields_set - {"reason"}
        if not fields:
            raise ValueError("Phải cung cấp ít nhất một trường cần điều chỉnh")
        return self


class AttendanceAdjustmentResponse(BaseModel):
    id: int
    attendance_daily_id: int
    admin_user_id: int
    admin_username: str
    reason: str
    before_data: dict
    after_data: dict
    created_at: datetime
