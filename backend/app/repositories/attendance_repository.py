from datetime import timedelta

from sqlalchemy import select

from backend.app.models import (
    AdminUser,
    AttendanceAdjustment,
    AttendanceDaily,
    AttendanceEvent,
    Employee,
    Shift,
)
from attendance.work_date_resolver import WorkDateResolver


class AttendanceRepository:
    @staticmethod
    def list_daily(
        db,
        date_from=None,
        date_to=None,
        employee_id=None,
        department=None,
        status=None,
    ):
        stmt = (
            select(AttendanceDaily, Employee, Shift)
            .join(Employee, Employee.id == AttendanceDaily.employee_id)
            .join(Shift, Shift.id == AttendanceDaily.shift_id)
            .order_by(AttendanceDaily.work_date.desc(), Employee.employee_code)
        )
        if date_from:
            stmt = stmt.where(AttendanceDaily.work_date >= date_from)
        if date_to:
            stmt = stmt.where(AttendanceDaily.work_date <= date_to)
        if employee_id:
            stmt = stmt.where(AttendanceDaily.employee_id == employee_id)
        if department:
            stmt = stmt.where(Employee.department == department)
        if status:
            stmt = stmt.where(AttendanceDaily.status == status)
        return list(db.execute(stmt).all())

    @staticmethod
    def get_daily_detail(db, daily_id, for_update=False):
        stmt = (
            select(AttendanceDaily, Employee, Shift)
            .join(Employee, Employee.id == AttendanceDaily.employee_id)
            .join(Shift, Shift.id == AttendanceDaily.shift_id)
            .where(AttendanceDaily.id == daily_id)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return db.execute(stmt).first()

    @staticmethod
    def get_events_for_daily(db, daily, shift):
        start = daily.work_date - timedelta(days=1)
        end = daily.work_date + timedelta(days=2)
        events = list(
            db.scalars(
                select(AttendanceEvent)
                .where(
                    AttendanceEvent.employee_id == daily.employee_id,
                    AttendanceEvent.recognized_at >= start,
                    AttendanceEvent.recognized_at < end,
                )
                .order_by(AttendanceEvent.recognized_at)
            )
        )
        return [
            event
            for event in events
            if WorkDateResolver.resolve(event.recognized_at, shift) == daily.work_date
        ]

    @staticmethod
    def create_adjustment(
        db, daily_id, admin_user_id, reason, before_data, after_data
    ):
        adjustment = AttendanceAdjustment(
            attendance_daily_id=daily_id,
            admin_user_id=admin_user_id,
            reason=reason,
            before_data=before_data,
            after_data=after_data,
        )
        db.add(adjustment)
        db.flush()
        return adjustment

    @staticmethod
    def list_adjustments(db, daily_id):
        return list(
            db.execute(
                select(AttendanceAdjustment, AdminUser.username)
                .join(AdminUser, AdminUser.id == AttendanceAdjustment.admin_user_id)
                .where(AttendanceAdjustment.attendance_daily_id == daily_id)
                .order_by(AttendanceAdjustment.created_at.desc())
            ).all()
        )

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
