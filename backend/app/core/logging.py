import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")

_STANDARD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
}
_REDACTED_FIELDS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "authorization",
    "cookie",
    "embedding",
    "frame",
    "image",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", request_id_context.get()),
            "event": getattr(record, "event", "application_log"),
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD_FIELDS or key in payload or key.startswith("_"):
                continue
            if key.lower() in _REDACTED_FIELDS:
                payload[key] = "[REDACTED]"
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_context.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestContextFilter())
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=[handler],
        force=True,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def log_extra(event: str, **fields) -> dict:
    """Build safe structured fields for business-event logs."""
    return {"event": event, **fields}
