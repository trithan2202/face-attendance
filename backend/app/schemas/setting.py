from datetime import datetime

from pydantic import BaseModel, Field


class SettingResponse(BaseModel):
    key: str
    value: str
    value_type: str
    group: str
    label: str
    description: str
    minimum: float
    maximum: float
    updated_at: datetime | None


class SettingUpdateRequest(BaseModel):
    value: str = Field(min_length=1, max_length=500)
