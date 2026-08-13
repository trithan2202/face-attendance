from sqlalchemy import select

from backend.app.models import (
    AttendanceDaily,
    AttendanceEvent
)


class AttendanceRepository:
    @staticmethod
    def get_daily(
        db,
        employee_id,
        work_date
    ):
        return db.scalar(
            select(AttendanceDaily).where(
                AttendanceDaily.employee_id
                == employee_id,
                AttendanceDaily.work_date
                == work_date
            )
        )

    @staticmethod
    def create_event(
        db,
        employee_id,
        event_type,
        recognized_at,
        similarity,
        detection_score=None,
        recognition_method="INSIGHTFACE"
    ):
        event = AttendanceEvent(
            employee_id=employee_id,
            event_type=event_type,
            recognized_at=recognized_at,
            similarity=similarity,
            detection_score=detection_score,
            recognition_method=recognition_method
        )

        db.add(event)
        db.flush()

        return event

    @staticmethod
    def create_daily(
        db,
        employee_id,
        shift_id,
        work_date,
        check_in,
        is_late,
        late_minutes
    ):
        daily = AttendanceDaily(
            employee_id=employee_id,
            shift_id=shift_id,
            work_date=work_date,
            first_check_in=check_in,
            status="MISSING_CHECK_OUT",
            is_late=is_late,
            late_minutes=late_minutes
        )

        db.add(daily)
        db.flush()

        return daily