from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from attendance.attendance_calculator import AttendanceCalculator
from backend.app.core.config import settings
from backend.app.repositories.attendance_repository import AttendanceRepository
from backend.app.core.logging import log_extra


logger = logging.getLogger("face_attendance.attendance_adjustment")


TRACKED_FIELDS = (
    "first_check_in",
    "last_check_out",
    "worked_minutes",
    "late_minutes",
    "early_leave_minutes",
    "overtime_minutes",
    "overtime_status",
    "status",
    "is_late",
    "is_early_leave",
    "is_overtime",
)


def snapshot(daily):
    result = {}
    for field in TRACKED_FIELDS:
        value = getattr(daily, field)
        result[field] = value.isoformat() if isinstance(value, datetime) else value
    return result


def local_naive(value):
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None)


class AttendanceAdjustmentService:
    @staticmethod
    def adjust(db, daily_id, admin_id, payload):
        row = AttendanceRepository.get_daily_detail(db, daily_id, for_update=True)
        if row is None:
            return None
        daily, employee, shift = row
        before = snapshot(daily)
        changes = payload.model_dump(exclude_unset=True, exclude={"reason"})
        for field in ("first_check_in", "last_check_out"):
            if field in changes:
                changes[field] = local_naive(changes[field])
        for field, value in changes.items():
            setattr(daily, field, value)

        if (
            daily.first_check_in is not None
            and daily.last_check_out is not None
            and daily.last_check_out < daily.first_check_in
        ):
            raise ValueError("Thời gian check-out phải sau check-in")

        AttendanceAdjustmentService._recalculate(daily, shift)
        if "status" in changes:
            daily.status = changes["status"]
        after = snapshot(daily)
        adjustment = AttendanceRepository.create_adjustment(
            db, daily.id, admin_id, payload.reason.strip(), before, after
        )
        db.commit()
        logger.info(
            "Attendance record adjusted",
            extra=log_extra(
                "attendance_adjusted",
                daily_id=daily.id,
                employee_id=employee.id,
                admin_id=admin_id,
                adjustment_id=adjustment.id,
                changed_fields=",".join(sorted(changes)),
                reason_length=len(payload.reason.strip()),
            ),
        )
        return daily, employee, shift, adjustment

    @staticmethod
    def _recalculate(daily, shift):
        AttendanceCalculator.recalculate(daily, shift)
