import calendar
import logging
import re
import threading
import time
from collections import deque
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.logging import log_extra
from backend.app.repositories.attendance_repository import AttendanceRepository
from backend.app.repositories.employee_repository import EmployeeRepository
from backend.app.schemas import (
    PublicAttendanceDay,
    PublicAttendanceResponse,
    PublicAttendanceSummary,
    PublicLookupRequest,
)


router = APIRouter(prefix="/public", tags=["public"])
logger = logging.getLogger("face_attendance.public")


MAX_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 60

_attempts = {}
_attempts_lock = threading.Lock()


def _rate_limit(employee_code):
    """Allow a handful of lookups per code per minute.

    Deliberately in-memory: this only has to slow down guessing on a single
    kiosk-style deployment, not survive a restart.
    """
    now = time.monotonic()
    with _attempts_lock:
        bucket = _attempts.setdefault(employee_code, deque())
        while bucket and now - bucket[0] > ATTEMPT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= MAX_ATTEMPTS:
            return False
        bucket.append(now)
        return True


def _digits_only(value):
    return re.sub(r"[^0-9]", "", value or "")


@router.post("/attendance-lookup", response_model=PublicAttendanceResponse)
def lookup_attendance(
    payload: PublicLookupRequest,
    db: Session = Depends(get_db),
):
    code = payload.employee_code.strip()

    if not _rate_limit(code):
        raise HTTPException(
            status_code=429,
            detail="Bạn đã thử quá nhiều lần, vui lòng đợi một phút",
        )

    # The same message for every failure so the form cannot be used to discover
    # which employee codes exist.
    invalid = HTTPException(
        status_code=404,
        detail="Mã nhân viên hoặc số CCCD không đúng",
    )

    employee = EmployeeRepository.get_by_code(db, code)
    if employee is None or employee.status == "INACTIVE":
        raise invalid
    if not employee.national_id:
        raise HTTPException(
            status_code=422,
            detail="Hồ sơ chưa có số CCCD, vui lòng liên hệ quản trị viên",
        )
    if _digits_only(employee.national_id) != _digits_only(payload.national_id):
        raise invalid

    start_date = date(payload.year, payload.month, 1)
    end_date = date(
        payload.year,
        payload.month,
        calendar.monthrange(payload.year, payload.month)[1],
    )
    rows = AttendanceRepository.list_daily(
        db,
        date_from=start_date,
        date_to=end_date,
        employee_id=employee.id,
    )

    days = []
    present_days = 0
    leave_days = 0
    late_days = 0
    total_worked = 0
    approved_overtime = 0

    for daily, _employee, _shift in sorted(rows, key=lambda row: row[0].work_date):
        days.append(
            PublicAttendanceDay(
                work_date=daily.work_date,
                check_in=daily.first_check_in,
                check_out=daily.last_check_out,
                worked_minutes=daily.worked_minutes,
                late_minutes=daily.late_minutes,
                overtime_minutes=daily.overtime_minutes,
                status=daily.status,
            )
        )
        if daily.status == "PRESENT":
            present_days += 1
        elif daily.status == "ON_LEAVE":
            leave_days += 1
        if daily.is_late:
            late_days += 1
        total_worked += daily.worked_minutes
        if daily.overtime_status == "APPROVED":
            approved_overtime += daily.overtime_minutes

    logger.info(
        "Public attendance lookup",
        extra=log_extra(
            "public_lookup",
            employee_id=employee.id,
            employee_code=employee.employee_code,
            year=payload.year,
            month=payload.month,
            day_count=len(days),
        ),
    )

    return PublicAttendanceResponse(
        employee_code=employee.employee_code,
        full_name=employee.full_name,
        department=employee.department.name if employee.department else None,
        shift_code=employee.shift.code if employee.shift else None,
        year=payload.year,
        month=payload.month,
        summary=PublicAttendanceSummary(
            present_days=present_days,
            leave_days=leave_days,
            late_days=late_days,
            total_worked_minutes=total_worked,
            approved_overtime_minutes=approved_overtime,
        ),
        days=days,
    )
