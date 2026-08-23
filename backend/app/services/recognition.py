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
from backend.app.services.face_engine_provider import get_face_engine
from backend.app.services.settings_service import SettingsService
from face_engine.matcher import FaceMatcher


logger = logging.getLogger("face_attendance.recognition")


# Why a recognised face did not turn into an attendance punch.
SUPPRESSED_MESSAGES = {
    "EMPLOYEE_NOT_FOUND": "Không tìm thấy hồ sơ nhân viên",
    "EMPLOYEE_NOT_ACTIVE": "Nhân viên đã ngưng hoạt động",
    "SHIFT_MISSING": "Nhân viên chưa được gán ca làm",
    "DUPLICATE_PUNCH": "Bạn vừa quét xong, vui lòng thử lại sau ít phút",
    "TOO_EARLY_CHECKOUT": "Chưa đến thời điểm có thể check-out",
}


@dataclass
class RecognitionSession:
    session_id: str
    created_at: float
    known_faces: dict
    metadata: dict
    state: str = "RECOGNIZING"
    message: str = "Giữ khuôn mặt trong khung hình"
    stable_since: float | None = None
    last_matched_at: float | None = None
    stable_seconds: float = 0.0
    employee_code: str | None = None
    full_name: str | None = None
    similarity: float | None = None
    event_type: str | None = None
    faces: list = field(default_factory=list)


class RecognitionService:
    def __init__(self, engine_factory=None, clock=None):
        self.engine_factory = engine_factory or get_face_engine
        self._engine = None
        self._sessions = {}
        self._lock = threading.RLock()
        self.clock = clock or time.monotonic
        self.matcher = FaceMatcher(settings.FACE_SIMILARITY_THRESHOLD)
        self.attendance = AttendanceService(
            settings.MIN_CHECKOUT_MINUTES,
            settings.MIN_PUNCH_INTERVAL_SECONDS,
            settings.OVERTIME_MIN_MINUTES,
        )
        self.hold_seconds = settings.RECOGNITION_HOLD_SECONDS

    def start(self, db):
        with self._lock:
            self._apply_settings(db)
            data = FaceRepository.get_centroids(db)
            session = RecognitionSession(
                session_id=secrets.token_urlsafe(24),
                created_at=self.clock(),
                known_faces={code: item["embedding"] for code, item in data.items()},
                metadata=data,
            )
            self._sessions[session.session_id] = session
            logger.info(
                "Recognition session started",
                extra=log_extra(
                    "recognition_started",
                    session_id=session.session_id,
                    known_employee_count=len(session.known_faces),
                    required_hold_seconds=self.hold_seconds,
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

            # Thresholds are read per frame so a change in the settings screen
            # takes effect without restarting the backend.
            self._apply_settings(db)

            faces = self._detect(frame)
            session.faces = self._face_boxes(frame, faces)
            if len(faces) != 1:
                previous_message = session.message
                self._reset_stability(session)
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
            session.similarity = similarity if similarity >= 0 else None
            if code is None:
                previous_message = session.message
                self._reset_stability(session)
                session.message = "Không nhận diện được nhân viên"
                if session.message != previous_message:
                    logger.info(
                        "Face was not matched",
                        extra=log_extra(
                            "recognition_not_matched",
                            session_id=session.session_id,
                            similarity=round(similarity, 4) if similarity >= 0 else None,
                            threshold=self.matcher.threshold,
                        ),
                    )
                return session
            now = self.clock()
            continuous = (
                session.employee_code == code
                and session.stable_since is not None
                and session.last_matched_at is not None
                and now - session.last_matched_at
                <= settings.RECOGNITION_MAX_FRAME_GAP_SECONDS
            )
            if not continuous:
                session.stable_since = now
                session.stable_seconds = 0.0
            else:
                session.stable_seconds = max(0.0, now - session.stable_since)
            session.last_matched_at = now
            session.employee_code = code
            session.full_name = session.metadata[code]["full_name"]
            if session.faces:
                session.faces[0]["label"] = session.full_name
                session.faces[0]["matched"] = True
            remaining = max(
                0.0, self.hold_seconds - session.stable_seconds
            )
            session.message = (
                "Đang xác nhận khuôn mặt "
                f"{session.stable_seconds:.1f}/{self.hold_seconds:g} giây"
            )
            logger.info(
                "Recognition match observed",
                extra=log_extra(
                    "recognition_match_observed",
                    session_id=session.session_id,
                    employee_code=code,
                    similarity=round(similarity, 4),
                    stable_seconds=round(session.stable_seconds, 2),
                    required_seconds=self.hold_seconds,
                    remaining_seconds=round(remaining, 2),
                ),
            )
            if session.stable_seconds >= self.hold_seconds:
                self._record_attendance(db, session, face)
            return session

    def expires_in(self, session):
        elapsed = self.clock() - session.created_at
        return max(
            0,
            math.ceil(settings.RECOGNITION_SESSION_TIMEOUT_SECONDS - elapsed),
        )

    def _apply_settings(self, db):
        self.matcher.threshold = SettingsService.get_float(
            db, "FACE_SIMILARITY_THRESHOLD"
        )
        self.hold_seconds = SettingsService.get_float(
            db, "RECOGNITION_HOLD_SECONDS"
        )
        self.attendance.min_checkout_minutes = SettingsService.get_int(
            db, "MIN_CHECKOUT_MINUTES"
        )
        self.attendance.min_punch_interval_seconds = SettingsService.get_int(
            db, "MIN_PUNCH_INTERVAL_SECONDS"
        )
        self.attendance.overtime_min_minutes = SettingsService.get_int(
            db, "OVERTIME_MIN_MINUTES"
        )

    def _detect(self, frame):
        if self._engine is None:
            self._engine = self.engine_factory()
        return self._engine.detect(frame)

    @staticmethod
    def _face_boxes(frame, faces):
        """Normalise detected boxes to 0..1 so the kiosk can overlay them."""
        height, width = frame.shape[:2]
        if not width or not height:
            return []

        def ratio(value, total):
            return min(1.0, max(0.0, float(value) / total))

        boxes = []
        for face in faces:
            x1, y1, x2, y2 = (float(value) for value in face.bbox)
            left = ratio(x1, width)
            top = ratio(y1, height)
            boxes.append(
                {
                    "x": round(left, 4),
                    "y": round(top, 4),
                    "width": round(min(ratio(x2, width) - left, 1.0 - left), 4),
                    "height": round(min(ratio(y2, height) - top, 1.0 - top), 4),
                    "score": round(float(face.det_score), 4),
                    "label": None,
                    "matched": False,
                }
            )
        return boxes

    @staticmethod
    def _reset_stability(session):
        session.stable_since = None
        session.last_matched_at = None
        session.stable_seconds = 0.0
        session.employee_code = None
        session.full_name = None
        session.similarity = None

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
        if result is None or result.get("event_type") is None:
            reason = (result or {}).get("reason", "UNKNOWN")
            session.state = "COOLDOWN"
            session.message = SUPPRESSED_MESSAGES.get(
                reason, "Chưa thể ghi nhận chấm công"
            )
            logger.info(
                "Attendance event suppressed",
                extra=log_extra(
                    "attendance_suppressed",
                    session_id=session.session_id,
                    employee_code=session.employee_code,
                    reason=reason,
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

    def _expired(self, session):
        return (
            session.state == "RECOGNIZING"
            and self.clock() - session.created_at
            > settings.RECOGNITION_SESSION_TIMEOUT_SECONDS
        )


recognition_service = RecognitionService()
