import time
import logging

import cv2

from backend.app.core.config import settings
from camera.capture import CameraCapture
from camera.embedding_cache import EmbeddingCache
from camera.stabilizer import RecognitionStabilizer
from face_engine import FaceEngine, FaceMatcher
from backend.app.services import WorkerStatusService
from backend.app.core.logging import log_extra


logger = logging.getLogger("face_attendance.worker")


class RecognitionWorker:
    def __init__(
        self,
        camera_source=0
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

        self.status = WorkerStatusService()
        self.last_heartbeat = 0.0

    def run(self):
        self.status.write("STARTING", False, True, "Worker đang khởi động")
        failed = False

        try:
            count = self.cache.refresh()

            logger.info(
                "Worker face cache loaded",
                extra=log_extra("worker_cache_loaded", employee_count=count),
            )

            self.camera.open()
            self._heartbeat(force=True)

            while True:
                self._heartbeat()
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

                cv2.imshow(
                    "Attendance Worker",
                    frame
                )

                if self._should_quit():
                    break

        except Exception as exc:
            failed = True
            self.status.write("ERROR", False, True, f"Worker lỗi: {type(exc).__name__}")
            logger.exception(
                "Recognition worker failed",
                extra=log_extra(
                    "worker_failed", exception_type=type(exc).__name__
                ),
            )
            raise
        finally:
            self.camera.release()
            cv2.destroyAllWindows()
            if not failed:
                self.status.write("STOPPED", False, True, "Worker đã dừng")
                logger.info("Recognition worker stopped", extra=log_extra("worker_stopped"))

    def _heartbeat(self, force=False):
        now = time.monotonic()
        if not force and now - self.last_heartbeat < 2:
            return
        self.status.write("READY", True, True, "Camera và model sẵn sàng")
        if force:
            logger.info("Recognition worker ready", extra=log_extra("worker_ready"))
        self.last_heartbeat = now

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
