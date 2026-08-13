from sqlalchemy import select

from backend.app.models import Shift


class ShiftRepository:
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