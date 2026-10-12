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
    overtime_status: str
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


class AttendanceSegment(BaseModel):
    """One in/out pair of a work day; `check_out` is null while still inside."""

    check_in: datetime
    check_out: datetime | None
    minutes: int


class AttendanceDetailResponse(BaseModel):
    daily: AttendanceDailyResponse
    events: list[AttendanceEventResponse]
    segments: list[AttendanceSegment]


class AttendanceAdjustmentRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    first_check_in: datetime | None = None
    last_check_out: datetime | None = None
    status: str | None = Field(
        default=None,
        pattern=r"^(PRESENT|MISSING_CHECK_IN|MISSING_CHECK_OUT|ABSENT|ON_LEAVE)$",
    )

    @model_validator(mode="after")
    def has_change(self):
        fields = self.model_fields_set - {"reason"}
        if not fields:
            raise ValueError("Phải cung cấp ít nhất một trường cần điều chỉnh")
        return self


class OvertimeDecisionRequest(BaseModel):
    status: str = Field(pattern=r"^(APPROVED|REJECTED)$")
    reason: str = Field(min_length=3, max_length=500)


class AttendanceAdjustmentResponse(BaseModel):
    id: int
    attendance_daily_id: int
    admin_user_id: int
    admin_username: str
    reason: str
    before_data: dict
    after_data: dict
    created_at: datetime


class LateTrendDay(BaseModel):
    work_date: date
    late_minutes: int
    late_count: int


class LateTrendMonth(BaseModel):
    year: int
    month: int
    late_minutes: int
    late_count: int


class LateTrendComparison(BaseModel):
    """Month-to-date late minutes against the same days of the previous month."""

    current_minutes: int
    previous_minutes: int
    change_percent: float | None
    days: int


class LateTrendResponse(BaseModel):
    daily: list[LateTrendDay]
    monthly: list[LateTrendMonth]
    comparison: LateTrendComparison
