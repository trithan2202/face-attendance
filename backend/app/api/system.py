from fastapi import APIRouter
from sqlalchemy import text

from backend.app.core.database import get_db_session
from backend.app.services import WorkerStatusService


router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    database = "up"
    db = get_db_session()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "down"
    finally:
        db.close()

    return {
        "status": "ok" if database == "up" else "degraded",
        "service": "face-attendance-api",
        "database": database,
    }


@router.get("/worker/status")
def worker_status():
    return WorkerStatusService().read()
