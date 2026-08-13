from pydantic import BaseModel


class EnrollmentSessionResponse(BaseModel):
    session_id: str
    employee_id: int
    state: str
    samples_collected: int
    target_samples: int
    message: str


class EnrollmentFrameResponse(EnrollmentSessionResponse):
    accepted: bool
    quality_score: float | None = None
    detection_score: float | None = None
