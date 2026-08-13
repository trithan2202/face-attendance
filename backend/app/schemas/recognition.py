from pydantic import BaseModel


class RecognitionStartRequest(BaseModel):
    liveness_session_id: str


class RecognitionSessionResponse(BaseModel):
    session_id: str
    state: str
    message: str
    stable_hits: int
    required_hits: int
    employee_code: str | None = None
    full_name: str | None = None
    similarity: float | None = None
    event_type: str | None = None
    expires_in_seconds: int
