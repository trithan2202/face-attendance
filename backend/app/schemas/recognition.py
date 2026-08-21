from pydantic import BaseModel


class FaceBox(BaseModel):
    """Face rectangle normalised to the submitted frame (0..1)."""

    x: float
    y: float
    width: float
    height: float
    score: float
    label: str | None = None
    matched: bool = False


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
    faces: list[FaceBox] = []
