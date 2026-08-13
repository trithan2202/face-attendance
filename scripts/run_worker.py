from backend.app.core.config import settings
from backend.app.core.logging import configure_logging
from backend.app.services import WorkerStatusService
from camera.worker import RecognitionWorker


def main():
    configure_logging(settings.LOG_LEVEL)
    status = WorkerStatusService()
    status.write("STARTING", False, False, "Đang tải model nhận diện")
    try:
        worker = RecognitionWorker(
            camera_source=settings.CAMERA_INDEX
        )
        worker.run()
    except Exception as exc:
        status.write("ERROR", False, False, f"Không thể chạy worker: {type(exc).__name__}")
        raise


if __name__ == "__main__":
    main()
