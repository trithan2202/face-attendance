import json
import os
from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.config import settings


class WorkerStatusService:
    def __init__(self, status_file: Path | None = None):
        self.status_file = status_file or settings.WORKER_STATUS_FILE

    def write(self, state: str, camera_ready: bool, model_ready: bool, message: str) -> None:
        payload = {
            "state": state,
            "camera_ready": camera_ready,
            "model_ready": model_ready,
            "message": message,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
        }
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.status_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.status_file)

    def read(self) -> dict:
        if not self.status_file.exists():
            return self._offline("Worker chưa được khởi động")
        try:
            payload = json.loads(self.status_file.read_text(encoding="utf-8"))
            updated_at = datetime.fromisoformat(payload["updated_at"])
            age = (datetime.now(timezone.utc) - updated_at).total_seconds()
            payload["online"] = age <= settings.WORKER_HEARTBEAT_TIMEOUT_SECONDS
            if not payload["online"]:
                payload["state"] = "OFFLINE"
                payload["message"] = "Worker đã ngừng gửi heartbeat"
            return payload
        except (OSError, ValueError, KeyError, TypeError):
            return self._offline("Không đọc được trạng thái worker")

    @staticmethod
    def _offline(message: str) -> dict:
        return {
            "online": False,
            "state": "OFFLINE",
            "camera_ready": False,
            "model_ready": False,
            "message": message,
            "updated_at": None,
            "pid": None,
        }
