import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_admin
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.repositories.employee_repository import EmployeeRepository
from backend.app.schemas import EnrollmentFrameResponse, EnrollmentSessionResponse
from backend.app.services.enrollment import TARGET_SAMPLES, enrollment_service
from backend.app.services.liveness import INSTRUCTIONS, LivenessEngineUnavailable


router = APIRouter(
    prefix="/admin",
    tags=["admin-enrollment"],
    dependencies=[Depends(get_current_admin)],
)


def _session_response(session):
    return EnrollmentSessionResponse(
        session_id=session.session_id,
        employee_id=session.employee_id,
        state=session.state,
        samples_collected=len(session.embeddings)
        if session.state == "CAPTURING"
        else TARGET_SAMPLES if session.state == "COMPLETED" else 0,
        target_samples=TARGET_SAMPLES,
        message=session.message,
        liveness_challenge=session.liveness_challenge,
        liveness_instruction=INSTRUCTIONS[session.liveness_challenge],
        liveness_progress=session.liveness_progress,
        liveness_required_progress=settings.LIVENESS_REQUIRED_FRAMES,
    )


@router.post(
    "/employees/{employee_id}/enrollment",
    response_model=EnrollmentSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_enrollment(employee_id: int, db: Session = Depends(get_db)):
    employee = EmployeeRepository.get_by_id(db, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    if employee.status == "INACTIVE":
        raise HTTPException(
            status_code=409,
            detail="Không thể đăng ký khuôn mặt cho nhân viên đã ngưng hoạt động",
        )
    return _session_response(enrollment_service.start(employee_id))


@router.get(
    "/enrollment/{session_id}", response_model=EnrollmentSessionResponse
)
def enrollment_status(session_id: str):
    session = enrollment_service.status(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên đăng ký")
    return _session_response(session)


@router.post(
    "/enrollment/{session_id}/frame", response_model=EnrollmentFrameResponse
)
async def submit_enrollment_frame(
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

    try:
        result = enrollment_service.process_frame(db, session_id, image)
    except LivenessEngineUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Dịch vụ liveness chưa sẵn sàng; hãy rebuild backend",
        ) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên đăng ký")
    session, accepted, quality_score, detection_score = result
    base = _session_response(session)
    return EnrollmentFrameResponse(
        **base.model_dump(),
        accepted=accepted,
        quality_score=quality_score,
        detection_score=detection_score,
    )


@router.delete(
    "/enrollment/{session_id}", response_model=EnrollmentSessionResponse
)
def cancel_enrollment(session_id: str):
    session = enrollment_service.cancel(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên đăng ký")
    return _session_response(session)
