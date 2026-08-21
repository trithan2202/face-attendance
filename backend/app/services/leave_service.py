import logging
from datetime import datetime, timedelta, timezone

from backend.app.core.logging import log_extra
from backend.app.models import AttendanceDaily
from backend.app.repositories.attendance_repository import AttendanceRepository
from backend.app.repositories.leave_request_repository import (
    LeaveRequestRepository,
)


logger = logging.getLogger("face_attendance.leave")

SUNDAY = 6


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def leave_dates(leave):
    """Every calendar day covered by the request, Sundays excluded.

    Sunday is the only non-working day the monthly report already treats as a
    weekend, so the two stay consistent.
    """
    current = leave.start_date
    while current <= leave.end_date:
        if current.weekday() != SUNDAY:
            yield current
        current += timedelta(days=1)


class LeaveService:
    @staticmethod
    def decide(db, leave_id, admin_id, payload):
        row = LeaveRequestRepository.get_detail(db, leave_id, for_update=True)
        if row is None:
            return None

        leave, employee, _created_by = row

        if leave.status != "PENDING":
            raise ValueError("Đơn nghỉ phép đã được xử lý")

        applied = 0
        skipped = 0

        if payload.status == "APPROVED":
            if employee.shift_id is None:
                raise ValueError("Nhân viên chưa được gán ca làm")
            applied, skipped = LeaveService._apply_leave_days(db, leave, employee)

        leave.status = payload.status
        leave.decided_by_admin_id = admin_id
        leave.decided_at = utc_now()
        leave.decision_note = payload.note.strip() if payload.note else None

        db.commit()

        logger.info(
            "Leave request decided",
            extra=log_extra(
                "leave_request_decided",
                leave_id=leave.id,
                employee_id=employee.id,
                employee_code=employee.employee_code,
                decision=leave.status,
                applied_days=applied,
                skipped_days=skipped,
            ),
        )

        return leave, employee, applied, skipped

    @staticmethod
    def _apply_leave_days(db, leave, employee):
        """Mark each covered day ON_LEAVE.

        A day that already carries a real check-in is left untouched: actual
        attendance always wins over a leave request.
        """
        applied = 0
        skipped = 0

        for work_date in leave_dates(leave):
            daily = AttendanceRepository.get_daily(db, employee.id, work_date)

            if daily is not None and daily.first_check_in is not None:
                skipped += 1
                continue

            if daily is None:
                daily = AttendanceDaily(
                    employee_id=employee.id,
                    shift_id=employee.shift_id,
                    work_date=work_date,
                    status="ON_LEAVE",
                )
                db.add(daily)
            else:
                daily.status = "ON_LEAVE"

            daily.last_check_out = None
            daily.worked_minutes = 0
            daily.late_minutes = 0
            daily.early_leave_minutes = 0
            daily.overtime_minutes = 0
            daily.is_late = False
            daily.is_early_leave = False
            daily.is_overtime = False
            applied += 1

        db.flush()

        return applied, skipped
