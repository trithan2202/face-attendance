import secrets
import logging
import threading
import time
from dataclasses import dataclass, field

import cv2
import numpy as np

from backend.app.core.config import settings
from backend.app.core.logging import log_extra
from backend.app.repositories.employee_repository import EmployeeRepository
from backend.app.repositories.face_repository import FaceRepository
from face_engine.quality import FaceQualityChecker
from face_engine.recognizer import FaceRecognizer


TARGET_SAMPLES = 10
logger = logging.getLogger("face_attendance.enrollment")


def create_face_engine():
    from face_engine.engine import FaceEngine

    return FaceEngine()


@dataclass
class EnrollmentSession:
    session_id: str
    employee_id: int
    created_at: float
    last_capture_at: float = 0.0
    state: str = "CAPTURING"
    message: str = "Đưa khuôn mặt vào giữa khung hình"
    embeddings: list[np.ndarray] = field(default_factory=list)
    quality_scores: list[float] = field(default_factory=list)
    detection_scores: list[float] = field(default_factory=list)


class EnrollmentSessionStore:
    def __init__(self):
        self._sessions = {}
        self._employee_sessions = {}
        self._lock = threading.RLock()

    def create(self, employee_id: int) -> EnrollmentSession:
        with self._lock:
            previous_id = self._employee_sessions.get(employee_id)
            if previous_id:
                self._sessions.pop(previous_id, None)
            session = EnrollmentSession(
                session_id=secrets.token_urlsafe(24),
                employee_id=employee_id,
                created_at=time.monotonic(),
            )
            self._sessions[session.session_id] = session
            self._employee_sessions[employee_id] = session.session_id
            logger.info(
                "Enrollment session started",
                extra=log_extra(
                    "enrollment_started",
                    session_id=session.session_id,
                    employee_id=employee_id,
                    target_samples=TARGET_SAMPLES,
                ),
            )
            return session

    def get(self, session_id: str) -> EnrollmentSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session and self._expired(session):
                session.state = "EXPIRED"
                session.message = "Phiên đăng ký đã hết hạn"
                session.embeddings.clear()
                logger.warning(
                    "Enrollment session expired",
                    extra=log_extra(
                        "enrollment_expired",
                        session_id=session.session_id,
                        employee_id=session.employee_id,
                    ),
                )
            return session

    def cancel(self, session_id: str) -> EnrollmentSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.state not in {"COMPLETED", "EXPIRED"}:
                session.state = "CANCELLED"
                session.message = "Đã hủy phiên đăng ký"
                session.embeddings.clear()
                logger.info(
                    "Enrollment session cancelled",
                    extra=log_extra(
                        "enrollment_cancelled",
                        session_id=session.session_id,
                        employee_id=session.employee_id,
                    ),
                )
            return session

    def lock(self):
        return self._lock

    @staticmethod
    def _expired(session):
        return (
            session.state == "CAPTURING"
            and time.monotonic() - session.created_at
            > settings.ENROLLMENT_SESSION_TIMEOUT_SECONDS
        )


class EnrollmentService:
    def __init__(self, store=None, engine_factory=None):
        self.store = store or EnrollmentSessionStore()
        self.engine_factory = engine_factory or create_face_engine
        self._engine = None
        self._engine_lock = threading.Lock()
        self.quality_checker = FaceQualityChecker()

    def start(self, employee_id: int):
        return self.store.create(employee_id)

    def status(self, session_id: str):
        return self.store.get(session_id)

    def cancel(self, session_id: str):
        return self.store.cancel(session_id)

    def process_frame(self, db, session_id: str, frame):
        with self.store.lock():
            session = self.store.get(session_id)
            if session is None:
                return None
            if session.state != "CAPTURING":
                return session, False, None, None

            now = time.monotonic()
            interval = settings.ENROLLMENT_CAPTURE_INTERVAL_MS / 1000
            if now - session.last_capture_at < interval:
                session.message = "Giữ yên và thay đổi nhẹ góc mặt"
                return session, False, None, None

            faces = self._detect(frame)
            if len(faces) == 0:
                session.message = "Không tìm thấy khuôn mặt"
                return session, False, None, None
            if len(faces) > 1:
                session.message = "Chỉ cho phép một khuôn mặt trong khung hình"
                return session, False, None, None

            face = faces[0]
            valid, message = self.quality_checker.check(frame, face)
            if not valid:
                session.message = message
                return session, False, None, float(face.det_score)

            quality_score = self._blur_score(frame, face)
            embedding = FaceRecognizer.normalize(face.embedding)
            session.embeddings.append(embedding)
            session.quality_scores.append(quality_score)
            session.detection_scores.append(float(face.det_score))
            session.last_capture_at = now
            session.message = f"Đã nhận mẫu {len(session.embeddings)}/{TARGET_SAMPLES}"
            logger.info(
                "Enrollment sample accepted",
                extra=log_extra(
                    "enrollment_sample_accepted",
                    session_id=session.session_id,
                    employee_id=session.employee_id,
                    samples_collected=len(session.embeddings),
                    target_samples=TARGET_SAMPLES,
                    quality_score=round(quality_score, 2),
                    detection_score=round(float(face.det_score), 4),
                ),
            )

            if len(session.embeddings) == TARGET_SAMPLES:
                self._complete(db, session)

            return session, True, quality_score, float(face.det_score)

    def _detect(self, frame):
        with self._engine_lock:
            if self._engine is None:
                self._engine = self.engine_factory()
            return self._engine.detect(frame)

    @staticmethod
    def _blur_score(frame, face):
        x1, y1, x2, y2 = face.bbox.astype(int)
        height, width = frame.shape[:2]
        crop = frame[max(0, y1):min(height, y2), max(0, x1):min(width, x2)]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    @staticmethod
    def _complete(db, session):
        employee = EmployeeRepository.get_by_id(db, session.employee_id)
        if employee is None or employee.status == "INACTIVE":
            session.state = "FAILED"
            session.message = "Nhân viên không tồn tại hoặc đã ngưng hoạt động"
            session.embeddings.clear()
            return

        centroid = FaceRecognizer.create_centroid(session.embeddings)
        try:
            FaceRepository.delete_employee_embeddings(db, employee.id)
            for index, embedding in enumerate(session.embeddings, start=1):
                FaceRepository.add_embedding(
                    db,
                    employee.id,
                    embedding,
                    sample_index=index,
                    quality_score=session.quality_scores[index - 1],
                    detection_score=session.detection_scores[index - 1],
                    is_centroid=False,
                )
            FaceRepository.add_embedding(
                db, employee.id, centroid, sample_index=None, is_centroid=True
            )
            employee.status = "ACTIVE"
            db.commit()
            session.state = "COMPLETED"
            session.message = "Đăng ký khuôn mặt thành công"
            session.embeddings.clear()
            logger.info(
                "Enrollment completed",
                extra=log_extra(
                    "enrollment_completed",
                    session_id=session.session_id,
                    employee_id=session.employee_id,
                    samples_saved=TARGET_SAMPLES,
                ),
            )
        except Exception:
            db.rollback()
            session.state = "FAILED"
            session.message = "Không thể lưu dữ liệu đăng ký"
            session.embeddings.clear()
            logger.exception(
                "Enrollment persistence failed",
                extra=log_extra(
                    "enrollment_failed",
                    session_id=session.session_id,
                    employee_id=session.employee_id,
                ),
            )
            raise


enrollment_service = EnrollmentService()
