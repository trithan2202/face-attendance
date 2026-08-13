from pydantic import BaseModel


class LivenessSessionResponse(BaseModel):
    session_id: str
    challenge: str
    instruction: str
    state: str
    message: str
    expires_in_seconds: int


class LivenessFrameResponse(LivenessSessionResponse):
    face_count: int
    progress: int
    required_progress: int
