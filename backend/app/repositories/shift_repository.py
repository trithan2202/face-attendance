from sqlalchemy import func, select

from backend.app.models import Employee, Shift


class ShiftRepository:
    @staticmethod
    def list_all(db):
        return list(db.scalars(select(Shift).order_by(Shift.code)))

    @staticmethod
    def get_by_code(db, code):
        return db.scalar(
            select(Shift).where(
                Shift.code == code
            )
        )

    @staticmethod
    def get_by_id(db, shift_id):
        return db.get(Shift, shift_id)

    @staticmethod
    def create(
        db,
        code,
        name,
        start_time,
        end_time,
        late_grace_minutes=0,
        early_leave_grace_minutes=0,
        cross_day=False
    ):
        shift = Shift(
            code=code,
            name=name,
            start_time=start_time,
            end_time=end_time,
            late_grace_minutes=late_grace_minutes,
            early_leave_grace_minutes=early_leave_grace_minutes,
            cross_day=cross_day
        )

        db.add(shift)
        db.flush()

        return shift

    @staticmethod
    def update(db, shift, **values):
        for field, value in values.items():
            setattr(shift, field, value)
        db.flush()
        return shift

    @staticmethod
    def employee_count(db, shift_id):
        return db.scalar(
            select(func.count(Employee.id)).where(Employee.shift_id == shift_id)
        ) or 0

    @staticmethod
    def delete(db, shift):
        db.delete(shift)
        db.flush()
