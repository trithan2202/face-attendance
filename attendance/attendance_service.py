from datetime import timedelta
import logging

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
from backend.app.core.logging import log_extra


logger = logging.getLogger("face_attendance.attendance")


def _suppressed(reason, **extra):
    """A scan that was recognised but deliberately not recorded."""
    return {"event_type": None, "reason": reason, **extra}


class AttendanceService:
    def __init__(
        self,
        min_checkout_minutes=60,
        min_punch_interval_seconds=60
    ):
        self.min_checkout_minutes = (
            min_checkout_minutes
        )
        self.min_punch_interval_seconds = (
            min_punch_interval_seconds
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
            logger.warning(
                "Attendance ignored because employee does not exist",
                extra=log_extra("attendance_ignored", employee_id=employee_id, reason="employee_not_found"),
            )
            return _suppressed("EMPLOYEE_NOT_FOUND")

        if employee.status != "ACTIVE":
            logger.warning(
                "Attendance ignored because employee is inactive",
                extra=log_extra("attendance_ignored", employee_id=employee_id, reason="employee_not_active"),
            )
            return _suppressed("EMPLOYEE_NOT_ACTIVE")

        if employee.shift is None:
            logger.warning(
                "Attendance ignored because employee has no shift",
                extra=log_extra("attendance_ignored", employee_id=employee_id, reason="shift_missing"),
            )
            return _suppressed("SHIFT_MISSING")

        shift = employee.shift

        work_date = WorkDateResolver.resolve(
            recognized_at,
            shift
        )

        events = AttendanceRepository.list_events_for_work_date(
            db,
            employee.id,
            work_date,
            shift
        )

        last_event = events[-1] if events else None

        # Guard against the same person being recognised repeatedly while they
        # stand in front of the kiosk.
        if last_event is not None:
            elapsed = (
                recognized_at - last_event.recognized_at
            ).total_seconds()

            if elapsed < self.min_punch_interval_seconds:
                logger.info(
                    "Punch ignored as duplicate",
                    extra=log_extra(
                        "attendance_duplicate_punch",
                        employee_id=employee.id,
                        work_date=work_date.isoformat(),
                        seconds_since_last=round(elapsed, 2),
                        min_interval=self.min_punch_interval_seconds,
                    ),
                )
                return _suppressed(
                    "DUPLICATE_PUNCH",
                    employee_id=employee.id
                )

        # Punches simply alternate: the first of the day is a check-in, and
        # every later scan flips the direction.
        event_type = (
            "CHECK_IN"
            if last_event is None
            or last_event.event_type == "CHECK_OUT"
            else "CHECK_OUT"
        )

        check_ins = [
            event
            for event in events
            if event.event_type == "CHECK_IN"
        ]
        check_outs = [
            event
            for event in events
            if event.event_type == "CHECK_OUT"
        ]

        # The minimum-shift-length rule still applies, but only to the first
        # check-out of the day; later ones are breaks.
        if (
            event_type == "CHECK_OUT"
            and not check_outs
            and check_ins
        ):
            earliest_checkout = (
                check_ins[0].recognized_at
                + timedelta(
                    minutes=self.min_checkout_minutes
                )
            )

            if recognized_at < earliest_checkout:
                logger.info(
                    "Checkout blocked by minimum interval",
                    extra=log_extra(
                        "attendance_checkout_too_early",
                        employee_id=employee.id,
                        work_date=work_date.isoformat(),
                        earliest_checkout=earliest_checkout.isoformat(),
                    ),
                )
                return _suppressed(
                    "TOO_EARLY_CHECKOUT",
                    employee_id=employee.id,
                    earliest_checkout=earliest_checkout
                )

        return self._record_punch(
            db,
            employee,
            shift,
            work_date,
            event_type,
            events,
            recognized_at,
            similarity,
            detection_score
        )

    def _record_punch(
        self,
        db,
        employee,
        shift,
        work_date,
        event_type,
        events,
        recognized_at,
        similarity,
        detection_score
    ):
        event = AttendanceRepository.create_event(
            db,
            employee.id,
            event_type,
            recognized_at,
            similarity,
            detection_score
        )

        daily = AttendanceRepository.get_daily(
            db,
            employee.id,
            work_date
        )

        if daily is None:
            daily = AttendanceRepository.create_daily(
                db,
                employee.id,
                shift.id,
                work_date,
                recognized_at,
                False,
                0
            )

        self._sync_daily(
            daily,
            events + [event],
            shift
        )

        db.commit()

        logger.info(
            "Attendance punch recorded",
            extra=log_extra(
                "attendance_punch_recorded",
                employee_id=employee.id,
                employee_code=employee.employee_code,
                daily_id=daily.id,
                work_date=work_date.isoformat(),
                event_type=event_type,
                punch_index=len(events) + 1,
                similarity=round(float(similarity), 4),
                worked_minutes=daily.worked_minutes,
                status=daily.status,
            ),
        )

        return {
            "event_type": event_type,
            "employee_id": employee.id,
            "daily_id": daily.id
        }

    @staticmethod
    def _sync_daily(daily, events, shift):
        """Rebuild the daily aggregate from every punch of the day.

        `first_check_in` and `last_check_out` stay the outer bounds of the day,
        so worked minutes keep the original meaning even with breaks in between.
        """
        check_ins = [
            event.recognized_at
            for event in events
            if event.event_type == "CHECK_IN"
        ]
        check_outs = [
            event.recognized_at
            for event in events
            if event.event_type == "CHECK_OUT"
        ]

        daily.first_check_in = min(check_ins) if check_ins else None
        daily.last_check_out = max(check_outs) if check_outs else None

        AttendanceCalculator.recalculate(daily, shift)
