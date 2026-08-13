from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ShiftBase(BaseModel):
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=100)
    start_time: time
    end_time: time
    late_grace_minutes: int = Field(default=0, ge=0, le=1440)
    early_leave_grace_minutes: int = Field(default=0, ge=0, le=1440)
    cross_day: bool = False

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time == self.end_time:
            raise ValueError("Giờ bắt đầu và kết thúc không được trùng nhau")
        if self.cross_day and self.end_time > self.start_time:
            raise ValueError("Ca qua ngày phải có giờ kết thúc nhỏ hơn giờ bắt đầu")
        if not self.cross_day and self.end_time < self.start_time:
            raise ValueError("Ca trong ngày phải có giờ kết thúc lớn hơn giờ bắt đầu")
        return self


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(ShiftBase):
    pass


class ShiftResponse(ShiftBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
