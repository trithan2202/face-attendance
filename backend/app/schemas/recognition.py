from pydantic import BaseModel


class RecognitionSessionResponse(BaseModel):
    session_id: str
    state: str
    message: str
    stable_seconds: float
    required_seconds: float
    employee_code: str | None = None
    full_name: str | None = None
    similarity: float | None = None
    event_type: str | None = None
    expires_in_seconds: int
