from pydantic import BaseModel


class EnrollmentSessionResponse(BaseModel):
    session_id: str
    employee_id: int
    state: str
    samples_collected: int
    target_samples: int
    message: str
    liveness_challenge: str | None = None
    liveness_instruction: str | None = None
    liveness_progress: int = 0
    liveness_required_progress: int = 0


class EnrollmentFrameResponse(EnrollmentSessionResponse):
    accepted: bool
    quality_score: float | None = None
    detection_score: float | None = None
