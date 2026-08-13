from datetime import timedelta

from attendance.attendance_calculator import (
    AttendanceCalculator
)
from attendance.work_date_resolver import (
    WorkDateResolver
)
from backend.app.models import Employee
from backend.app.repositories.attendance_repository import (
    AttendanceRepository
)


class AttendanceService:
    def __init__(
        self,
        min_checkout_minutes=60
    ):
        self.min_checkout_minutes = (
            min_checkout_minutes
        )

    def process(
        self,
        db,
        employee_id,
        recognized_at,
        similarity,
        detection_score=None
    ):
        employee = db.get(
            Employee,
            employee_id
        )

        if employee is None:
            return None

        if employee.status != "ACTIVE":
            return None

        if employee.shift is None:
            return None

        shift = employee.shift

        work_date = WorkDateResolver.resolve(
            recognized_at,
            shift
        )

        daily = AttendanceRepository.get_daily(
            db,
            employee.id,
            work_date
        )

        if daily is None:
            return self._check_in(
                db,
                employee,
                shift,
                work_date,
                recognized_at,
                similarity,
                detection_score
            )

        if (
            daily.first_check_in is not None
            and daily.last_check_out is None
        ):
            earliest_checkout = (
                daily.first_check_in
                + timedelta(
                    minutes=self.min_checkout_minutes
                )
            )

            if recognized_at < earliest_checkout:
                return None

            return self._check_out(
                db,
                daily,
                employee,
                shift,
                work_date,
                recognized_at,
                similarity,
                detection_score
            )

        return None

    def _check_in(
        self,
        db,
        employee,
        shift,
        work_date,
        recognized_at,
        similarity,
        detection_score
    ):
        is_late, late_minutes = (
            AttendanceCalculator.calculate_late(
                recognized_at,
                work_date,
                shift
            )
        )

        AttendanceRepository.create_event(
            db,
            employee.id,
            "CHECK_IN",
            recognized_at,
            similarity,
            detection_score
        )

        daily = (
            AttendanceRepository.create_daily(
                db,
                employee.id,
                shift.id,
                work_date,
                recognized_at,
                is_late,
                late_minutes
            )
        )

        db.commit()

        return {
            "event_type": "CHECK_IN",
            "employee_id": employee.id,
            "daily_id": daily.id
        }

    def _check_out(
        self,
        db,
        daily,
        employee,
        shift,
        work_date,
        recognized_at,
        similarity,
        detection_score
    ):
        metrics = (
            AttendanceCalculator.calculate_checkout(
                daily.first_check_in,
                recognized_at,
                work_date,
                shift
            )
        )

        AttendanceRepository.create_event(
            db,
            employee.id,
            "CHECK_OUT",
            recognized_at,
            similarity,
            detection_score
        )

        daily.last_check_out = recognized_at
        daily.worked_minutes = (
            metrics["worked_minutes"]
        )
        daily.is_early_leave = (
            metrics["is_early_leave"]
        )
        daily.early_leave_minutes = (
            metrics["early_leave_minutes"]
        )
        daily.is_overtime = (
            metrics["is_overtime"]
        )
        daily.overtime_minutes = (
            metrics["overtime_minutes"]
        )
        daily.status = "PRESENT"

        db.commit()

        return {
            "event_type": "CHECK_OUT",
            "employee_id": employee.id,
            "daily_id": daily.id
        }