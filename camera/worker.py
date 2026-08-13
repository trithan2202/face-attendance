import time
from datetime import datetime

import cv2

from attendance.attendance_service import (
    AttendanceService
)
from backend.app.core.config import settings
from backend.app.core.database import (
    get_db_session
)
from camera.capture import CameraCapture
from camera.embedding_cache import EmbeddingCache
from camera.stabilizer import RecognitionStabilizer
from face_engine import FaceEngine, FaceMatcher


class RecognitionWorker:
    def __init__(
        self,
        camera_source=0,
        cooldown_seconds=10,
        min_checkout_minutes=60
    ):
        self.camera = CameraCapture(
            camera_source
        )

        self.engine = FaceEngine()

        self.matcher = FaceMatcher(
            threshold=(
                settings.FACE_SIMILARITY_THRESHOLD
            )
        )

        self.cache = EmbeddingCache()

        self.stabilizer = RecognitionStabilizer(
            window_size=5,
            required_hits=3
        )

        self.attendance = AttendanceService(
            min_checkout_minutes=(
                min_checkout_minutes
            )
        )

        self.cooldown_seconds = (
            cooldown_seconds
        )

        self.last_processed = {}

    def run(self):
        count = self.cache.refresh()

        print(
            f"[INFO] Loaded {count} employees"
        )

        self.camera.open()

        try:
            while True:
                ok, frame = self.camera.read()

                if not ok:
                    continue

                faces = self.engine.detect(frame)

                if len(faces) != 1:
                    self.stabilizer.update(None)

                    cv2.imshow(
                        "Attendance Worker",
                        frame
                    )

                    if self._should_quit():
                        break

                    continue

                face = faces[0]

                employee_code, similarity = (
                    self.matcher.match(
                        face.embedding,
                        self.cache.known_faces
                    )
                )

                confirmed_code = (
                    self.stabilizer.update(
                        employee_code
                    )
                )

                self._draw(
                    frame,
                    face,
                    employee_code,
                    similarity,
                    confirmed_code
                )

                if confirmed_code:
                    self._process_attendance(
                        confirmed_code,
                        similarity,
                        float(face.det_score)
                    )

                cv2.imshow(
                    "Attendance Worker",
                    frame
                )

                if self._should_quit():
                    break

        finally:
            self.camera.release()
            cv2.destroyAllWindows()

    def _process_attendance(
        self,
        employee_code,
        similarity,
        detection_score
    ):
        now_monotonic = time.monotonic()

        last = self.last_processed.get(
            employee_code
        )

        if (
            last is not None
            and now_monotonic - last
            < self.cooldown_seconds
        ):
            return

        employee = self.cache.get_employee(
            employee_code
        )

        if employee is None:
            return

        db = get_db_session()

        try:
            result = self.attendance.process(
                db,
                employee_id=(
                    employee["employee_id"]
                ),
                recognized_at=datetime.now(),
                similarity=similarity,
                detection_score=detection_score
            )

            if result:
                self.last_processed[
                    employee_code
                ] = now_monotonic

                print(
                    f"[ATTENDANCE] "
                    f"{employee_code} "
                    f"{result['event_type']}"
                )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    @staticmethod
    def _draw(
        frame,
        face,
        employee_code,
        similarity,
        confirmed_code
    ):
        x1, y1, x2, y2 = (
            face.bbox.astype(int)
        )

        if employee_code is None:
            color = (0, 0, 255)
            label = (
                f"Unknown | {similarity:.3f}"
            )
        else:
            color = (0, 255, 255)
            label = (
                f"{employee_code} | "
                f"{similarity:.3f}"
            )

        if confirmed_code:
            color = (0, 255, 0)
            label += " | CONFIRMED"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            frame,
            label,
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2,
            cv2.LINE_AA
        )

    @staticmethod
    def _should_quit():
        return (
            cv2.waitKey(1) & 0xFF
        ) == ord("q")