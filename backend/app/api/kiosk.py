import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.core.config import settings
from backend.app.schemas import (
    LivenessFrameResponse,
    LivenessSessionResponse,
    RecognitionSessionResponse,
    RecognitionStartRequest,
)
from backend.app.core.database import get_db
from backend.app.services.recognition import recognition_service
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.app.services.liveness import (
    INSTRUCTIONS,
    LivenessEngineUnavailable,
    liveness_service,
)


router = APIRouter(prefix="/kiosk", tags=["kiosk"])


def _response(session):
    return LivenessSessionResponse(
        session_id=session.session_id,
        challenge=session.challenge,
        instruction=INSTRUCTIONS[session.challenge],
        state=session.state,
        message=session.message,
        expires_in_seconds=liveness_service.expires_in(session),
    )


@router.post(
    "/liveness",
    response_model=LivenessSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_liveness():
    return _response(liveness_service.start())


@router.get("/liveness/{session_id}", response_model=LivenessSessionResponse)
def liveness_status(session_id: str):
    session = liveness_service.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên liveness")
    return _response(session)


@router.post(
    "/liveness/{session_id}/frame", response_model=LivenessFrameResponse
)
async def submit_liveness_frame(
    session_id: str,
    frame: UploadFile = File(...),
):
    if frame.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Frame phải là ảnh JPEG, PNG hoặc WebP")
    data = await frame.read(settings.MAX_FRAME_BYTES + 1)
    if len(data) > settings.MAX_FRAME_BYTES:
        raise HTTPException(status_code=413, detail="Frame vượt quá kích thước cho phép")
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=422, detail="Không thể giải mã frame")

    try:
        result = liveness_service.process_frame(session_id, image)
    except LivenessEngineUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Dịch vụ liveness chưa sẵn sàng; hãy rebuild backend",
        ) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên liveness")
    session, face_count = result
    base = _response(session)
    return LivenessFrameResponse(
        **base.model_dump(),
        face_count=face_count,
        progress=session.progress,
        required_progress=settings.LIVENESS_REQUIRED_FRAMES,
    )


@router.delete("/liveness/{session_id}", response_model=LivenessSessionResponse)
def cancel_liveness(session_id: str):
    session = liveness_service.cancel(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên liveness")
    return _response(session)


def _recognition_response(session):
    return RecognitionSessionResponse(
        session_id=session.session_id,
        state=session.state,
        message=session.message,
        stable_hits=session.stable_hits,
        required_hits=3,
        employee_code=session.employee_code,
        full_name=session.full_name,
        similarity=session.similarity,
        event_type=session.event_type,
        expires_in_seconds=recognition_service.expires_in(session),
    )


@router.post(
    "/recognition",
    response_model=RecognitionSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_recognition(
    payload: RecognitionStartRequest,
    db: Session = Depends(get_db),
):
    proof = liveness_service.consume_passed(payload.liveness_session_id)
    if proof is None:
        raise HTTPException(
            status_code=409,
            detail="Liveness chưa đạt, đã hết hạn hoặc đã được sử dụng",
        )
    return _recognition_response(
        recognition_service.start(db, payload.liveness_session_id)
    )


@router.get(
    "/recognition/{session_id}", response_model=RecognitionSessionResponse
)
def recognition_status(session_id: str):
    session = recognition_service.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên nhận diện")
    return _recognition_response(session)


@router.post(
    "/recognition/{session_id}/frame", response_model=RecognitionSessionResponse
)
async def submit_recognition_frame(
    session_id: str,
    frame: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if frame.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Frame phải là ảnh JPEG, PNG hoặc WebP")
    data = await frame.read(settings.MAX_FRAME_BYTES + 1)
    if len(data) > settings.MAX_FRAME_BYTES:
        raise HTTPException(status_code=413, detail="Frame vượt quá kích thước cho phép")
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=422, detail="Không thể giải mã frame")
    session = recognition_service.process_frame(db, session_id, image)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên nhận diện")
    return _recognition_response(session)
