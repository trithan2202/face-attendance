import math
import logging
import random
import secrets
import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np

from backend.app.core.config import settings
from backend.app.core.logging import log_extra


logger = logging.getLogger("face_attendance.liveness")


BLINK = "BLINK"
TURN_LEFT = "TURN_LEFT"
TURN_RIGHT = "TURN_RIGHT"
CHALLENGES = (BLINK, TURN_LEFT, TURN_RIGHT)
INSTRUCTIONS = {
    BLINK: "Hãy chớp mắt một lần",
    TURN_LEFT: "Hãy quay đầu sang trái",
    TURN_RIGHT: "Hãy quay đầu sang phải",
}

LEFT_EYE = (33, 160, 158, 133, 153, 144)
RIGHT_EYE = (362, 385, 387, 263, 373, 380)
LEFT_CHEEK = 234
RIGHT_CHEEK = 454
NOSE_TIP = 1


class LivenessEngineUnavailable(RuntimeError):
    """Raised when the installed MediaPipe package cannot provide Face Mesh."""


@dataclass
class LivenessSession:
    session_id: str
    challenge: str
    created_at: float
    state: str = "WAITING"
    message: str = "Đưa khuôn mặt vào giữa khung hình"
    progress: int = 0
    saw_open_eyes: bool = False
    saw_closed_eyes: bool = False
    passed_at: float | None = None


class FaceMeshAnalyzer:
    def __init__(self):
        self._mesh = None

    def analyze(self, frame):
        if self._mesh is None:
            try:
                import mediapipe as mp

                face_mesh = mp.solutions.face_mesh
            except (ImportError, AttributeError) as exc:
                raise LivenessEngineUnavailable(
                    "MediaPipe Face Mesh is unavailable. Install the dependency "
                    "version pinned in requirements.txt and rebuild the backend image."
                ) from exc

            self._mesh = face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=2,
                refine_landmarks=True,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6,
            )
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._mesh.process(rgb)
        if not result.multi_face_landmarks:
            return []
        return [
            [(point.x, point.y) for point in face.landmark]
            for face in result.multi_face_landmarks
        ]


class LivenessService:
    def __init__(self, analyzer=None, challenge_picker=None):
        self.analyzer = analyzer or FaceMeshAnalyzer()
        self.challenge_picker = challenge_picker or (lambda: random.choice(CHALLENGES))
        self._sessions = {}
        self._lock = threading.RLock()

    def start(self):
        with self._lock:
            challenge = self.challenge_picker()
            session = LivenessSession(
                session_id=secrets.token_urlsafe(24),
                challenge=challenge,
                created_at=time.monotonic(),
                message=INSTRUCTIONS[challenge],
            )
            self._sessions[session.session_id] = session
            logger.info(
                "Liveness session started",
                extra=log_extra(
                    "liveness_started",
                    session_id=session.session_id,
                    challenge=challenge,
                    timeout_seconds=settings.LIVENESS_TIMEOUT_SECONDS,
                ),
            )
            return session

    def get(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
            if session and self._is_expired(session):
                session.state = "FAILED"
                session.message = "Thử thách đã hết thời gian"
                logger.warning(
                    "Liveness session expired",
                    extra=log_extra(
                        "liveness_expired",
                        session_id=session.session_id,
                        challenge=session.challenge,
                    ),
                )
            return session

    def cancel(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.state == "WAITING":
                session.state = "CANCELLED"
                session.message = "Đã hủy thử thách liveness"
                logger.info(
                    "Liveness session cancelled",
                    extra=log_extra(
                        "liveness_cancelled",
                        session_id=session.session_id,
                        challenge=session.challenge,
                    ),
                )
            return session

    def consume_passed(self, session_id):
        with self._lock:
            session = self.get(session_id)
            if session is None or session.state != "PASSED":
                return None
            session.state = "CONSUMED"
            session.message = "Kết quả liveness đã được dùng để nhận diện"
            logger.info(
                "Liveness proof consumed",
                extra=log_extra(
                    "liveness_consumed",
                    session_id=session.session_id,
                    challenge=session.challenge,
                ),
            )
            return session

    def process_frame(self, session_id, frame):
        with self._lock:
            session = self.get(session_id)
            if session is None:
                return None
            if session.state != "WAITING":
                return session, 0
            previous_message = session.message
            if min(frame.shape[:2]) < 160:
                session.message = "Khung hình quá nhỏ"
                session.progress = 0
                self._log_frame_state(session, previous_message, 0)
                return session, 0
            blur = cv2.Laplacian(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F
            ).var()
            if blur < 40:
                session.message = "Hình ảnh bị mờ"
                session.progress = 0
                self._log_frame_state(session, previous_message, 0)
                return session, 0

            try:
                faces = self.analyzer.analyze(frame)
            except LivenessEngineUnavailable:
                logger.exception(
                    "Liveness engine unavailable",
                    extra=log_extra(
                        "liveness_engine_unavailable",
                        session_id=session.session_id,
                    ),
                )
                raise
            if len(faces) != 1:
                session.progress = 0
                session.message = (
                    "Không tìm thấy khuôn mặt"
                    if not faces
                    else "Chỉ cho phép một khuôn mặt trong khung hình"
                )
                self._log_frame_state(session, previous_message, len(faces))
                return session, len(faces)

            self._advance(session, faces[0])
            self._log_frame_state(session, previous_message, 1)
            return session, 1

    @staticmethod
    def _log_frame_state(session, previous_message, face_count):
        if session.state == "PASSED":
            logger.info(
                "Liveness challenge passed",
                extra=log_extra(
                    "liveness_passed",
                    session_id=session.session_id,
                    challenge=session.challenge,
                    progress=session.progress,
                ),
            )
        elif session.message != previous_message:
            logger.info(
                "Liveness state changed",
                extra=log_extra(
                    "liveness_state_changed",
                    session_id=session.session_id,
                    challenge=session.challenge,
                    state=session.state,
                    face_count=face_count,
                    progress=session.progress,
                    reason=session.message,
                ),
            )

    def expires_in(self, session):
        elapsed = time.monotonic() - session.created_at
        return max(0, math.ceil(settings.LIVENESS_TIMEOUT_SECONDS - elapsed))

    @staticmethod
    def _eye_aspect_ratio(points, indices):
        eye = [np.asarray(points[index], dtype=np.float32) for index in indices]
        vertical = np.linalg.norm(eye[1] - eye[5]) + np.linalg.norm(eye[2] - eye[4])
        horizontal = 2 * np.linalg.norm(eye[0] - eye[3])
        return float(vertical / horizontal) if horizontal else 0.0

    def _advance(self, session, points):
        if session.challenge == BLINK:
            left = self._eye_aspect_ratio(points, LEFT_EYE)
            right = self._eye_aspect_ratio(points, RIGHT_EYE)
            eyes_open = (left + right) / 2 > settings.LIVENESS_BLINK_EAR_THRESHOLD
            if eyes_open and not session.saw_closed_eyes:
                session.saw_open_eyes = True
                session.message = "Bây giờ hãy chớp mắt"
            elif not eyes_open and session.saw_open_eyes:
                session.saw_closed_eyes = True
                session.message = "Mở mắt trở lại"
            elif eyes_open and session.saw_closed_eyes:
                self._pass(session)
            return

        left_x = points[LEFT_CHEEK][0]
        right_x = points[RIGHT_CHEEK][0]
        width = right_x - left_x
        if abs(width) < 1e-6:
            session.progress = 0
            return
        ratio = (points[NOSE_TIP][0] - left_x) / width
        threshold = settings.LIVENESS_HEAD_TURN_RATIO
        matched = (
            session.challenge == TURN_LEFT and ratio < threshold
        ) or (
            session.challenge == TURN_RIGHT and ratio > 1 - threshold
        )
        session.progress = session.progress + 1 if matched else 0
        session.message = INSTRUCTIONS[session.challenge]
        if session.progress >= settings.LIVENESS_REQUIRED_FRAMES:
            self._pass(session)

    @staticmethod
    def _pass(session):
        session.state = "PASSED"
        session.message = "Đã hoàn thành thử thách liveness"
        session.passed_at = time.monotonic()

    @staticmethod
    def _is_expired(session):
        if session.state == "WAITING":
            return (
                time.monotonic() - session.created_at
                > settings.LIVENESS_TIMEOUT_SECONDS
            )
        if session.state == "PASSED" and session.passed_at is not None:
            return (
                time.monotonic() - session.passed_at
                > settings.LIVENESS_PROOF_TTL_SECONDS
            )
        return False


liveness_service = LivenessService()
