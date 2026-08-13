import math
import logging
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from attendance.attendance_service import AttendanceService
from backend.app.core.config import settings
from backend.app.core.logging import log_extra
from backend.app.repositories.face_repository import FaceRepository
from camera.stabilizer import RecognitionStabilizer
from face_engine.matcher import FaceMatcher


def create_face_engine():
    from face_engine.engine import FaceEngine

    return FaceEngine()


logger = logging.getLogger("face_attendance.recognition")


@dataclass
class RecognitionSession:
    session_id: str
    liveness_session_id: str
    created_at: float
    known_faces: dict
    metadata: dict
    state: str = "RECOGNIZING"
    message: str = "Giữ khuôn mặt ổn định trước camera"
    stable_hits: int = 0
    employee_code: str | None = None
    full_name: str | None = None
    similarity: float | None = None
    event_type: str | None = None
    stabilizer: RecognitionStabilizer = field(
        default_factory=lambda: RecognitionStabilizer(window_size=5, required_hits=3)
    )


class RecognitionService:
    def __init__(self, engine_factory=None):
        self.engine_factory = engine_factory or create_face_engine
        self._engine = None
        self._sessions = {}
        self._lock = threading.RLock()
        self.matcher = FaceMatcher(settings.FACE_SIMILARITY_THRESHOLD)
        self.attendance = AttendanceService(settings.MIN_CHECKOUT_MINUTES)

    def start(self, db, liveness_session_id):
        with self._lock:
            data = FaceRepository.get_centroids(db)
            session = RecognitionSession(
                session_id=secrets.token_urlsafe(24),
                liveness_session_id=liveness_session_id,
                created_at=time.monotonic(),
                known_faces={code: item["embedding"] for code, item in data.items()},
                metadata=data,
            )
            self._sessions[session.session_id] = session
            logger.info(
                "Recognition session started",
                extra=log_extra(
                    "recognition_started",
                    session_id=session.session_id,
                    liveness_session_id=liveness_session_id,
                    known_employee_count=len(session.known_faces),
                ),
            )
            return session

    def get(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
            if session and self._expired(session):
                session.state = "FAILED"
                session.message = "Phiên nhận diện đã hết thời gian"
                logger.warning(
                    "Recognition session expired",
                    extra=log_extra(
                        "recognition_expired", session_id=session.session_id
                    ),
                )
            return session

    def process_frame(self, db, session_id, frame):
        with self._lock:
            session = self.get(session_id)
            if session is None:
                return None
            if session.state != "RECOGNIZING":
                return session

            faces = self._detect(frame)
            if len(faces) != 1:
                previous_message = session.message
                session.stabilizer.reset()
                session.stable_hits = 0
                session.message = (
                    "Không tìm thấy khuôn mặt"
                    if not faces
                    else "Chỉ cho phép một khuôn mặt trong khung hình"
                )
                if session.message != previous_message:
                    logger.info(
                        "Recognition frame rejected",
                        extra=log_extra(
                            "recognition_frame_rejected",
                            session_id=session.session_id,
                            face_count=len(faces),
                            reason=session.message,
                        ),
                    )
                return session

            face = faces[0]
            code, similarity = self.matcher.match(face.embedding, session.known_faces)
            confirmed = session.stabilizer.update(code)
            session.stable_hits = (
                sum(value == code for value in session.stabilizer.history) if code else 0
            )
            session.similarity = similarity if similarity >= 0 else None
            if code is None:
                previous_message = session.message
                session.message = "Không nhận diện được nhân viên"
                if session.message != previous_message:
                    logger.info(
                        "Face was not matched",
                        extra=log_extra(
                            "recognition_not_matched",
                            session_id=session.session_id,
                            similarity=round(similarity, 4) if similarity >= 0 else None,
                            threshold=settings.FACE_SIMILARITY_THRESHOLD,
                        ),
                    )
                return session
            session.employee_code = code
            session.full_name = session.metadata[code]["full_name"]
            session.message = f"Đang xác nhận {session.stable_hits}/3"
            logger.info(
                "Recognition match observed",
                extra=log_extra(
                    "recognition_match_observed",
                    session_id=session.session_id,
                    employee_code=code,
                    similarity=round(similarity, 4),
                    stable_hits=session.stable_hits,
                    required_hits=3,
                ),
            )
            if confirmed:
                self._record_attendance(db, session, face)
            return session

    def expires_in(self, session):
        elapsed = time.monotonic() - session.created_at
        return max(
            0,
            math.ceil(settings.RECOGNITION_SESSION_TIMEOUT_SECONDS - elapsed),
        )

    def _detect(self, frame):
        if self._engine is None:
            self._engine = self.engine_factory()
        return self._engine.detect(frame)

    def _record_attendance(self, db, session, face):
        employee = session.metadata[session.employee_code]
        local_now = datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)
        result = self.attendance.process(
            db,
            employee_id=employee["employee_id"],
            recognized_at=local_now,
            similarity=session.similarity,
            detection_score=float(face.det_score),
        )
        if result is None:
            session.state = "COOLDOWN"
            session.message = "Chưa đến thời điểm có thể check-out"
            logger.info(
                "Attendance event suppressed by cooldown",
                extra=log_extra(
                    "attendance_cooldown",
                    session_id=session.session_id,
                    employee_code=session.employee_code,
                ),
            )
            return
        session.state = "COMPLETED"
        session.event_type = result["event_type"]
        session.message = (
            "Check-in thành công"
            if session.event_type == "CHECK_IN"
            else "Check-out thành công"
        )
        logger.info(
            "Recognition and attendance completed",
            extra=log_extra(
                "recognition_completed",
                session_id=session.session_id,
                employee_code=session.employee_code,
                similarity=round(session.similarity, 4),
                attendance_event=session.event_type,
            ),
        )

    @staticmethod
    def _expired(session):
        return (
            session.state == "RECOGNIZING"
            and time.monotonic() - session.created_at
            > settings.RECOGNITION_SESSION_TIMEOUT_SECONDS
        )


recognition_service = RecognitionService()
