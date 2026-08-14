import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self):
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://face_user:face_password@localhost:5432/face_attendance",
        )

        self.CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
        self.FACE_SIMILARITY_THRESHOLD = float(
            os.getenv("FACE_SIMILARITY_THRESHOLD", "0.50")
        )
        self.TIMEZONE = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
        self.JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-env")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
        self.ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
        self.LIVENESS_TIMEOUT_SECONDS = int(
            os.getenv("LIVENESS_TIMEOUT_SECONDS", "15")
        )
        self.LIVENESS_BLINK_EAR_THRESHOLD = float(
            os.getenv("LIVENESS_BLINK_EAR_THRESHOLD", "0.20")
        )
        self.LIVENESS_HEAD_TURN_RATIO = float(
            os.getenv("LIVENESS_HEAD_TURN_RATIO", "0.38")
        )
        self.LIVENESS_REQUIRED_FRAMES = int(
            os.getenv("LIVENESS_REQUIRED_FRAMES", "3")
        )
        self.LIVENESS_PROOF_TTL_SECONDS = int(
            os.getenv("LIVENESS_PROOF_TTL_SECONDS", "10")
        )
        self.RECOGNITION_SESSION_TIMEOUT_SECONDS = int(
            os.getenv("RECOGNITION_SESSION_TIMEOUT_SECONDS", "30")
        )
        self.RECOGNITION_HOLD_SECONDS = float(
            os.getenv("RECOGNITION_HOLD_SECONDS", "3")
        )
        self.RECOGNITION_MAX_FRAME_GAP_SECONDS = float(
            os.getenv("RECOGNITION_MAX_FRAME_GAP_SECONDS", "1")
        )
        self.MIN_CHECKOUT_MINUTES = int(os.getenv("MIN_CHECKOUT_MINUTES", "60"))
        self.ENROLLMENT_SESSION_TIMEOUT_SECONDS = int(
            os.getenv("ENROLLMENT_SESSION_TIMEOUT_SECONDS", "180")
        )
        self.ENROLLMENT_CAPTURE_INTERVAL_MS = int(
            os.getenv("ENROLLMENT_CAPTURE_INTERVAL_MS", "500")
        )
        self.MAX_FRAME_BYTES = int(os.getenv("MAX_FRAME_BYTES", "5242880"))
        self.WORKER_HEARTBEAT_TIMEOUT_SECONDS = int(
            os.getenv("WORKER_HEARTBEAT_TIMEOUT_SECONDS", "10")
        )
        self.WORKER_STATUS_FILE = Path(
            os.getenv(
                "WORKER_STATUS_FILE",
                str(PROJECT_ROOT / "runtime" / "worker-status.json"),
            )
        )
        origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
        )
        self.CORS_ORIGINS = [
            item.strip() for item in origins.split(",") if item.strip()
        ]
        self.DEBUG = _get_bool("DEBUG", False)
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_HTTP_FRAME_REQUESTS = _get_bool("LOG_HTTP_FRAME_REQUESTS", False)

settings = Settings()
