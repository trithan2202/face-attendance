import logging

from backend.app.core.logging import log_extra
from backend.app.repositories.attendance_repository import AttendanceRepository
from backend.app.services.attendance_adjustment import snapshot


logger = logging.getLogger("face_attendance.overtime")


class OvertimeApprovalService:
    @staticmethod
    def decide(db, daily_id, admin_id, payload):
        """Approve or reject the overtime recorded on a work day.

        The decision is written into the existing attendance audit trail rather
        than a table of its own, so it shows up in the record's history next to
        manual time edits.
        """
        row = AttendanceRepository.get_daily_detail(db, daily_id, for_update=True)
        if row is None:
            return None

        daily, employee, shift = row

        if daily.overtime_minutes <= 0:
            raise ValueError("Ngày công này không có giờ tăng ca")
        if daily.overtime_status not in {"PENDING", "APPROVED", "REJECTED"}:
            raise ValueError("Trạng thái tăng ca không hợp lệ")

        before = snapshot(daily)
        daily.overtime_status = payload.status
        after = snapshot(daily)

        adjustment = AttendanceRepository.create_adjustment(
            db, daily.id, admin_id, payload.reason.strip(), before, after
        )
        db.commit()

        logger.info(
            "Overtime decision recorded",
            extra=log_extra(
                "overtime_decided",
                daily_id=daily.id,
                employee_id=employee.id,
                employee_code=employee.employee_code,
                admin_id=admin_id,
                adjustment_id=adjustment.id,
                decision=daily.overtime_status,
                overtime_minutes=daily.overtime_minutes,
            ),
        )

        return daily, employee, shift, adjustment
